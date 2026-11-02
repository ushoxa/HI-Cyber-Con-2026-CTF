#include <openssl/bn.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>
#include <time.h>
static volatile sig_atomic_t stopping=0;
static void handler(int sig){stopping=1;}
static void checkpoint(const char *path,uint64_t done,BIGNUM *x){
 char tmp[4096];snprintf(tmp,sizeof(tmp),"%s.tmp",path);FILE *f=fopen(tmp,"w");if(!f){perror(tmp);exit(3);}
 char *s=BN_bn2hex(x);fprintf(f,"%llu %s\n",(unsigned long long)done,s);OPENSSL_free(s);fclose(f);
 if(rename(tmp,path)){perror(path);exit(4);}
}
int main(int argc,char **argv){
 if(argc!=6){fprintf(stderr,"usage: %s modulus.hex seed.hex rounds checkpoint output\n",argv[0]);return 1;}
 char nhex[1024],ahex[1024],xhex[1024];FILE *f=fopen(argv[1],"r");if(!f)return 2;fscanf(f,"%1023s",nhex);fclose(f);
 f=fopen(argv[2],"r");if(!f)return 2;fscanf(f,"%1023s",ahex);fclose(f);
 BIGNUM *n=NULL,*a=NULL,*x=BN_new();BN_hex2bn(&n,nhex);BN_hex2bn(&a,ahex);
 BN_CTX *ctx=BN_CTX_new();BN_MONT_CTX *mont=BN_MONT_CTX_new();if(!BN_MONT_CTX_set(mont,n,ctx))return 2;
 if(!BN_to_montgomery(x,a,mont,ctx))return 2;
 uint64_t done=0,count=strtoull(argv[3],NULL,10);f=fopen(argv[4],"r");
 if(f){unsigned long long prev=0;if(fscanf(f,"%llu %1023s",&prev,xhex)!=2 || prev>count)return 2;done=prev;BN_hex2bn(&x,xhex);fclose(f);}
 fprintf(stderr,"resuming at %llu/%llu\n",(unsigned long long)done,(unsigned long long)count);fflush(stderr);
 signal(SIGINT,handler);signal(SIGTERM,handler);
 uint64_t start=done;struct timespec t0,t1;clock_gettime(CLOCK_MONOTONIC,&t0);
 while(done<count){uint64_t batch=count-done;if(batch>10000000)batch=10000000;
  for(uint64_t j=0;j<batch;j++){if(!BN_mod_mul_montgomery(x,x,x,mont,ctx))return 2;}
  done+=batch;checkpoint(argv[4],done,x);clock_gettime(CLOCK_MONOTONIC,&t1);
  double sec=t1.tv_sec-t0.tv_sec+(t1.tv_nsec-t0.tv_nsec)/1e9;double rate=(done-start)/sec;
  fprintf(stderr,"progress %llu/%llu (%.2f%%), %.0f rounds/s, ETA %.0f s\n",(unsigned long long)done,(unsigned long long)count,100.0*done/count,rate,(count-done)/rate);fflush(stderr);
  if(stopping)return 130;
 }
 if(!BN_from_montgomery(a,x,mont,ctx))return 2;char *s=BN_bn2hex(a);
 f=fopen(argv[5],"w");if(!f)return 2;fprintf(f,"%s\n",s);fclose(f);OPENSSL_free(s);
 BN_free(x);BN_free(a);BN_free(n);BN_CTX_free(ctx);BN_MONT_CTX_free(mont);return 0;
}