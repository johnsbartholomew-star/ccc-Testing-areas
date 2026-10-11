// Synthetic native-tokenizer and context-capacity integration test. No service.
#include "llama.h"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>
#include <sys/resource.h>
using Clock = std::chrono::steady_clock;
static double seconds(Clock::time_point start) { return std::chrono::duration<double>(Clock::now()-start).count(); }
static void check(bool ok, const char *msg) { if (!ok) throw std::runtime_error(msg); }
static std::vector<llama_token> tokenize(const llama_vocab *v, const std::string &s) {
    int n = llama_tokenize(v,s.data(),static_cast<int32_t>(s.size()),nullptr,0,false,false);
    check(n<0,"native_tokenizer_count_failed");
    std::vector<llama_token> t(static_cast<size_t>(-n));
    int actual=llama_tokenize(v,s.data(),static_cast<int32_t>(s.size()),t.data(),static_cast<int32_t>(t.size()),false,false);
    check(actual==static_cast<int>(t.size()),"native_tokenizer_count_mismatch"); return t;
}
static std::string piece(const llama_vocab *v,llama_token t) {
    std::vector<char> b(256); int n=llama_token_to_piece(v,t,b.data(),static_cast<int32_t>(b.size()),0,false);
    if(n<0) { b.resize(static_cast<size_t>(-n)); n=llama_token_to_piece(v,t,b.data(),static_cast<int32_t>(b.size()),0,false); }
    check(n>=0,"detokenization_failed"); return std::string(b.data(),static_cast<size_t>(n));
}
int main(int argc,char **argv) {
    std::cout.setf(std::ios::unitbuf);
    llama_model *model=nullptr; llama_context *ctx=nullptr; llama_batch_ext *batch=nullptr; llama_sampler *sampler=nullptr;
    try {
        check(argc==4,"usage_probe_model_prompt_output_prefix");
        constexpr int INPUT=49152, RESERVE=4096, CONTEXT=INPUT+RESERVE, OUTPUT=16, BATCH=512;
        std::ifstream in(argv[2],std::ios::binary); check(bool(in),"prompt_missing");
        std::string source((std::istreambuf_iterator<char>(in)),{}); auto total_start=Clock::now();
        llama_backend_init(); auto mp=llama_model_default_params(); mp.n_gpu_layers=0;
        auto load_start=Clock::now(); model=llama_model_load_from_file(argv[1],mp); check(model!=nullptr,"model_load_failed");
        double load_seconds=seconds(load_start); const auto *v=llama_model_get_vocab(model);
        int trained=llama_model_n_ctx_train(model);
        std::cout<<"{\"stage\":\"model_loaded\",\"load_seconds\":"<<load_seconds<<",\"model_context\":"<<trained<<",\"model_load_mode\":"<<int(mp.load_mode)<<"}\n";
        check(trained>=CONTEXT,"model_context_below_requirement");
        auto tokens=tokenize(v,source); check(tokens.size()>=INPUT,"synthetic_source_too_short");
        tokens.resize(INPUT); std::string input_text;
        for(auto t:tokens) input_text+=piece(v,t);
        check(tokenize(v,input_text)==tokens,"native_tokenizer_roundtrip_mismatch");
        std::string prefix=argv[3];
        { std::ofstream f(prefix+".input.txt",std::ios::binary); f<<input_text; check(bool(f),"input_write_failed"); }
        { std::ofstream f(prefix+".input.tokens"); for(auto t:tokens) f<<t<<'\n'; check(bool(f),"token_write_failed"); }
        auto cp=llama_context_default_params(); cp.n_ctx=CONTEXT; cp.n_batch=BATCH; cp.n_ubatch=128;
        cp.n_seq_max=1; cp.n_threads=4; cp.n_threads_batch=4; cp.no_perf=false;
        cp.type_k=GGML_TYPE_F16; cp.type_v=GGML_TYPE_F16; cp.offload_kqv=false; cp.op_offload=false;
        cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_ENABLED;
        auto ctx_start=Clock::now(); ctx=llama_init_from_model(model,cp); check(ctx!=nullptr,"context_allocation_failed");
        double context_seconds=seconds(ctx_start); check(llama_n_ctx(ctx)>=CONTEXT,"runtime_context_below_requirement");
        std::cout<<"{\"stage\":\"tokenizer_and_context\",\"input_tokens\":"<<tokens.size()<<",\"generation_reserve\":"<<RESERVE<<",\"runtime_context\":"<<llama_n_ctx(ctx)<<",\"context_seconds\":"<<context_seconds<<",\"roundtrip_equal\":true,\"add_special\":false,\"parse_special\":false}\n";
        batch=llama_batch_ext_init(ctx); check(batch!=nullptr,"batch_allocation_failed");
        auto decode=[&](const llama_token *t,int count,int pos0) {
            llama_batch_ext_clear(batch);
            for(int i=0;i<count;++i) { int idx=llama_batch_ext_add_token(batch,0,t[i]); llama_pos pos=pos0+i; llama_batch_ext_set_pos(batch,idx,&pos); }
            llama_batch_ext_set_output_logits(batch,count-1,true);
            check(llama_process(ctx,LLAMA_PROCESS_TYPE_DECODE,batch)==0,"native_decode_failed");
        };
        auto prefill_start=Clock::now();
        for(int pos=0;pos<INPUT;pos+=BATCH) {
            int count=std::min(BATCH,INPUT-pos); decode(tokens.data()+pos,count,pos);
            if((pos+count)%4096==0) std::cout<<"{\"stage\":\"prefill_progress\",\"processed_tokens\":"<<pos+count<<",\"elapsed_seconds\":"<<seconds(prefill_start)<<"}\n";
        }
        double prefill_seconds=seconds(prefill_start); sampler=llama_sampler_init_greedy();
        check(sampler!=nullptr,"sampler_failed"); std::vector<llama_token> output; std::string text;
        auto generation_start=Clock::now();
        for(int i=0;i<OUTPUT;++i) {
            auto token=llama_sampler_sample(sampler,ctx,-1); llama_sampler_accept(sampler,token);
            output.push_back(token); text+=piece(v,token); decode(&token,1,INPUT+i);
            if(llama_vocab_is_eog(v,token)) break;
        }
        double generation_seconds=seconds(generation_start); check(!output.empty(),"no_generated_tokens");
        { std::ofstream f(prefix+".output.txt",std::ios::binary); f<<text; check(bool(f),"output_write_failed"); }
        { std::ofstream f(prefix+".output.tokens"); for(auto t:output) f<<t<<'\n'; check(bool(f),"output_token_write_failed"); }
        struct rusage usage{}; check(getrusage(RUSAGE_SELF,&usage)==0,"peak_rss_unavailable");
        std::cout<<"{\"stage\":\"result\",\"status\":\"PASS\",\"processed_input_tokens\":"<<INPUT<<",\"generated_tokens\":"<<output.size()<<",\"prefill_seconds\":"<<prefill_seconds<<",\"prefill_tokens_per_second\":"<<INPUT/prefill_seconds<<",\"generation_seconds\":"<<generation_seconds<<",\"generation_tokens_per_second\":"<<output.size()/generation_seconds<<",\"peak_rss_kib\":"<<usage.ru_maxrss<<",\"total_seconds\":"<<seconds(total_start)<<"}\n";
        llama_batch_ext_free(batch); llama_sampler_free(sampler); llama_free(ctx); llama_model_free(model); llama_backend_free(); return 0;
    } catch(const std::exception &e) {
        std::cerr<<"PREFLIGHT_FAIL: "<<e.what()<<'\n';
        if(batch) llama_batch_ext_free(batch); if(sampler) llama_sampler_free(sampler);
        if(ctx) llama_free(ctx); if(model) llama_model_free(model); llama_backend_free(); return 1;
    }
}
