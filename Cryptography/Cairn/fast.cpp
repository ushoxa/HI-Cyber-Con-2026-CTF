#include <array>
#include <vector>
#include <algorithm>
#include <cassert>
#include <cstring>
#include <cstdio>
#include <chrono>
#include <fstream>
#include <random>
#include <gmp.h>
#include <openssl/sha.h>
using U=uint64_t; using W=__uint128_t;
constexpr U C=4294968273ULL;
struct Fp {
    U v[4]{};
    Fp(U x=0) {v[0]=x;}
    bool operator==(const Fp& b)const{return !memcmp(v,b.v,32);}
    bool zero()const{return !(v[0]|v[1]|v[2]|v[3]);}
    bool operator<(const Fp& b)const{for(int i=3;i>=0;--i)if(v[i]!=b.v[i])return v[i]<b.v[i];return false;}
    void normalize(){if(v[3]==~U(0)&&v[2]==~U(0)&&v[1]==~U(0)&&v[0]>=U(0)-C){v[0]+=C;v[1]=v[2]=v[3]=0;}}
    static Fp fold(Fp a,U h){
        while(h){W z=W(h)*C+a.v[0];a.v[0]=z;h=z>>64;for(int i=1;i<4&&h;++i){z=W(a.v[i])+h;a.v[i]=z;h=z>>64;}}
        a.normalize();return a;
    }
    Fp operator+(const Fp& b)const{
        Fp r;U h=0;for(int i=0;i<4;++i){W z=W(v[i])+b.v[i]+h;r.v[i]=z;h=z>>64;}return fold(r,h);
    }
    Fp operator-(const Fp& b)const{
        Fp r;U h=0;for(int i=0;i<4;++i){W sub=W(b.v[i])+h;r.v[i]=v[i]-U(sub);h=(W(v[i])<sub);}
        if(h){W sub=C;for(int i=0;i<4;++i){U old=r.v[i];r.v[i]-=U(sub);sub=(W(old)<sub);}}return r;
    }
    Fp operator-()const{return Fp()-*this;}
    Fp operator*(const Fp& b)const{
        U t[8]{};
        for(int i=0;i<4;++i){U h=0;for(int k=0;k<4;++k){W z=W(v[i])*b.v[k]+t[i+k]+h;t[i+k]=z;h=z>>64;}t[i+4]=h;}
        Fp r;U h=0;for(int i=0;i<4;++i){W z=W(t[i+4])*C+t[i]+h;r.v[i]=z;h=z>>64;}return fold(r,h);
    }
    Fp pow(const U* e,int n)const{Fp r(1);for(int i=n*64-1;i>=0;--i){r=r*r;if((e[i/64]>>(i%64))&1)r=r*(*this);}return r;}
    Fp inv()const{
        assert(!zero());mpz_t a,p,b;mpz_inits(a,p,b,nullptr);mpz_import(a,4,-1,8,0,0,v);mpz_set_ui(p,1);mpz_mul_2exp(p,p,256);mpz_sub_ui(p,p,C);int ok=mpz_invert(b,a,p);assert(ok);Fp r;size_t n;mpz_export(r.v,&n,-1,8,0,0,b);mpz_clears(a,p,b,nullptr);return r;
    }
    Fp sqrt()const{const U e[4]={0xffffffffbfffff0cULL,~U(0),~U(0),0x3fffffffffffffffULL};return pow(e,4);}
    static Fp read(const char* s){mpz_t a;mpz_init_set_str(a,s,10);mpz_t p;mpz_init_set_ui(p,1);mpz_mul_2exp(p,p,256);mpz_sub_ui(p,p,C);mpz_mod(a,a,p);Fp r;size_t n;mpz_export(r.v,&n,-1,8,0,0,a);mpz_clears(a,p,nullptr);return r;}
    std::string str()const{mpz_t a;mpz_init(a);mpz_import(a,4,-1,8,0,0,v);char* s=mpz_get_str(nullptr,10,a);std::string r(s);free(s);mpz_clear(a);return r;}
};
struct Fq {
    Fp a,b;
    Fq(U x=0):a(x){} Fq(Fp x,Fp y):a(x),b(y){}
    bool zero()const{return a.zero()&&b.zero();}
    bool operator==(const Fq& z)const{return a==z.a&&b==z.b;}
    bool operator<(const Fq& z)const{return a<z.a||(a==z.a&&b<z.b);}
    Fq operator+(const Fq& z)const{return {a+z.a,b+z.b};}
    Fq operator-(const Fq& z)const{return {a-z.a,b-z.b};}
    Fq operator-()const{return {-a,-b};}
    Fq operator*(const Fq& z)const{Fp ac=a*z.a,bd=b*z.b;return {ac-bd,(a+b)*(z.a+z.b)-ac-bd};}
    Fq sq()const{Fp ab=a*b;return {(a+b)*(a-b),ab+ab};}
    Fq inv()const{Fp n=(a*a+b*b).inv();return {a*n,-b*n};}
    Fq operator/(const Fq& z)const{return *this*z.inv();}
    Fq pow(const U* e,int n)const{Fq r(1);for(int i=n*64-1;i>=0;--i){r=r.sq();if((e[i/64]>>(i%64))&1)r=r*(*this);}return r;}
    Fq cube_root()const{const U e[8]={0xc71c7379555891ebULL,0x38e38e38e38e38e3ULL,0xe38e38e38e38e38eULL,0x8e38e38e38e38e38ULL,0x38e38e3871c71abfULL,0xe38e38e38e38e38eULL,0x8e38e38e38e38e38ULL,0x38e38e38e38e38e3ULL};Fq r=pow(e,8);assert(r.sq()*r==*this);return r;}
    Fq sqrt()const{
        if(b.zero()){Fp x=a.sqrt();if(x*x==a)return {x,0};return {0,(-a).sqrt()};}
        static Fp half=Fp(2).inv();Fp norm=(a*a+b*b).sqrt();Fp s=(a+norm)*half;Fp x=s.sqrt();if(!(x*x==s)){s=(a-norm)*half;x=s.sqrt();}assert(x*x==s);return {x,b*(x+x).inv()};
    }
};
template<int N> void square_poly(Fq* out,const Fq* in){
    if constexpr(N==1){out[0]=in[0].sq();out[1]=Fq();}
    else{
        std::array<Fq,N> lo{},hi{},mid{};std::array<Fq,N/2> sum{};
        for(int k=0;k<N/2;++k)sum[k]=in[k]+in[k+N/2];
        square_poly<N/2>(lo.data(),in);square_poly<N/2>(hi.data(),in+N/2);square_poly<N/2>(mid.data(),sum.data());
        for(int k=0;k<2*N;++k)out[k]=Fq();
        for(int k=0;k<N;++k){out[k]=out[k]+lo[k];out[k+N/2]=out[k+N/2]+mid[k]-lo[k]-hi[k];out[k+N]=out[k+N]+hi[k];}
    }
}
struct Poly {
    std::array<Fq,17> c{};int d=-1;
    void trim(){while(d>=0&&c[d].zero())--d;}
    void monic(){trim();if(d>=0&&!(c[d]==Fq(1))){Fq iv=c[d].inv();for(int i=0;i<=d;++i)c[i]=c[i]*iv;}}
    Poly rem(const Poly& f)const{Poly r=*this;for(int k=r.d;k>=f.d;--k){Fq v=r.c[k];if(!v.zero())for(int j=0;j<f.d;++j)r.c[k-f.d+j]=r.c[k-f.d+j]-v*f.c[j];r.c[k]=Fq();}r.d=std::min(r.d,f.d-1);r.trim();return r;}
    Poly sqmod(const Poly& f)const{Poly r;r.d=2*d;for(int i=0;i<=d;++i){r.c[2*i]=r.c[2*i]+c[i].sq();for(int j=0;j<i;++j){Fq v=c[i]*c[j];r.c[i+j]=r.c[i+j]+v+v;}}return r.rem(f);}
    Poly linear_mod(Fq a,const Poly& f)const{Poly r;r.d=d+1;for(int i=0;i<=d;++i){r.c[i+1]=r.c[i+1]+c[i];r.c[i]=r.c[i]+c[i]*a;}return r.rem(f);}
    Poly gcd(Poly b)const{Poly a=*this;a.monic();b.monic();while(b.d>=0){Poly r=a.rem(b);a=b;b=r;b.monic();}return a;}
    Poly div(const Poly& f)const{Poly r=*this,q;q.d=d-f.d;for(int k=d;k>=f.d;--k){Fq v=r.c[k];q.c[k-f.d]=v;for(int j=0;j<=f.d;++j)r.c[k-f.d+j]=r.c[k-f.d+j]-v*f.c[j];}r.trim();assert(r.d==-1);q.trim();return q;}
    Fq eval(Fq z)const{Fq r;for(int i=d;i>=0;--i)r=r*z+c[i];return r;}
};
std::mt19937_64 rng(1234567);
Fp random_fp(){Fp x;for(auto& v:x.v)v=rng();x.normalize();return x;}
void split(const Poly& f,std::vector<Fq>& roots);
void split_character(const Poly& f,Poly g,Fq zeta,int level,std::vector<Fq>& roots){
    if(f.d<=4||level==0){split(f,roots);return;}
    Poly h=g;for(int k=1;k<level;++k)h=h.sqmod(f);
    h.c[0]=h.c[0]-Fq(1);h.trim();Poly even=f.gcd(h);
    Fq next=zeta.sq();
    if(even.d==f.d){split_character(f,g,next,level-1,roots);return;}
    Fq inverse=zeta.inv();
    if(even.d==0){for(int k=0;k<=g.d;++k)g.c[k]=g.c[k]*inverse;split_character(f,g,next,level-1,roots);return;}
    Poly odd=f.div(even),ge=g.rem(even),go=g.rem(odd);
    for(int k=0;k<=go.d;++k)go.c[k]=go.c[k]*inverse;
    split_character(even,ge,next,level-1,roots);split_character(odd,go,next,level-1,roots);
}
void split(const Poly& f,std::vector<Fq>& roots){
    if(f.d==1){roots.push_back(-f.c[0]);return;}
    if(f.d==2){Fq b=f.c[1],s=(b.sq()-Fq(4)*f.c[0]).sqrt();static Fq half=Fq(2).inv();roots.push_back((-b+s)*half);roots.push_back((-b-s)*half);return;}
    if(f.d==3){
        static Fq third=Fq(3).inv(),half=Fq(2).inv();
        static Fq omega(Fp::read("55594575648329892869085402983802832744385952214688224221778511981742606582254"),0);
        Fq b=f.c[2],a=f.c[1]-b.sq()*third;
        Fq c=f.c[0]-b*f.c[1]*third+Fq(2)*b.sq()*b*third*third*third;
        Fq d=(c.sq()*half*half+a.sq()*a*third*third*third).sqrt();
        Fq t=-c*half+d;if(t.zero())t=-c*half-d;
        Fq u=t.cube_root(),v=-a*third/u;
        for(int k=0;k<3;++k){roots.push_back(u+v-b*third);u=u*omega;v=v*omega.sq();}return;
    }
    if(f.d==4){
        static Fq half=Fq(2).inv(),quarter=Fq(4).inv(),sixteenth=Fq(16).inv(),inv256=Fq(256).inv();
        Fq b=f.c[3],c=f.c[2],d=f.c[1],e=f.c[0],b2=b.sq();
        Fq p=c-Fq(3)*b2*Fq(8).inv();
        Fq q=d-b*c*half+b2*b*Fq(8).inv();
        Fq r=e-b*d*quarter+b2*c*sixteenth-Fq(3)*b2.sq()*inv256;
        std::vector<Fq> rr;
        if(q.zero()){
            Poly g;g.d=2;g.c[0]=r;g.c[1]=p;g.c[2]=Fq(1);std::vector<Fq> s;split(g,s);
            for(Fq z:s){Fq v=z.sqrt();rr.push_back(v);rr.push_back(-v);}
        }else{
            Poly g;g.d=3;g.c[0]=-q.sq();g.c[1]=p.sq()-Fq(4)*r;g.c[2]=Fq(2)*p;g.c[3]=Fq(1);std::vector<Fq> s;split(g,s);
            Fq z=s[0];if(z.zero())z=s[1];Fq v=z.sqrt(),u=(z+p)*half,w=-q*half/v;
            Poly g1;g1.d=2;g1.c[2]=Fq(1);g1.c[1]=-v;g1.c[0]=u-w;split(g1,rr);
            g1.c[1]=v;g1.c[0]=u+w;split(g1,rr);
        }
        for(Fq z:rr)roots.push_back(z-b*quarter);return;
    }
    const U exp[8]={0x800003d10007485ULL,0,0,0xf000000000000000ULL,0xffffffffefffffc2ULL,~U(0),~U(0),0x7ffffffffffffffULL};
    static Fq zeta(Fp::read("80118438774556531143242904366909950766932388749389140702743450968206219689180"),Fp::read("46225217980340384269731736594336672407758460493230126383022590574903230077976"));
    Fq a(random_fp(),random_fp());Poly g;g.d=0;g.c[0]=Fq(1);for(int k=506;k>=0;--k){g=g.sqmod(f);if((exp[k/64]>>(k%64))&1)g=g.linear_mod(a,f);}
    split_character(f,g,zeta,5,roots);
}
struct Term{int x,y;Fp k;};
std::array<std::vector<Term>,8> terms;
std::vector<Fq> get_roots(Fq z,int l,const Fq* known=nullptr){
    std::array<Fq,9> powers;powers[0]=Fq(1);for(int i=1;i<=l+1;++i)powers[i]=powers[i-1]*z;Poly f;f.d=l+1;
    for(auto& t:terms[l])f.c[t.y]=f.c[t.y]+powers[t.x]*Fq(t.k,0);
    Poly df;df.d=f.d-1;for(int k=1;k<=f.d;++k)df.c[k-1]=f.c[k]*Fq(k);df.monic();Poly g=f.gcd(df);if(g.d>0)f=f.div(g);
    Poly original=f;std::vector<Fq> r;
    if(known){assert(f.eval(*known).zero());Poly factor;factor.d=1;factor.c[0]=-*known;factor.c[1]=Fq(1);f=f.div(factor);r.push_back(*known);}
    if(f.d>0)split(f,r);std::sort(r.begin(),r.end());assert(int(r.size())==original.d);for(auto& v:r)assert(original.eval(v).zero());return r;
}
void test_fp(){
    for(int i=0;i<10000;++i){Fp a=random_fp(),b=random_fp();mpz_t x,y,p,z;mpz_inits(x,y,p,z,nullptr);mpz_import(x,4,-1,8,0,0,a.v);mpz_import(y,4,-1,8,0,0,b.v);mpz_set_ui(p,1);mpz_mul_2exp(p,p,256);mpz_sub_ui(p,p,C);
        Fp r=a*b;mpz_mul(z,x,y);mpz_mod(z,z,p);Fp expected;size_t n;mpz_export(expected.v,&n,-1,8,0,0,z);assert(r==expected);assert((a+b)-b==a);assert((a-b)+b==a);if(i<100){Fp s=(a*a).sqrt();assert(s*s==a*a);Fq v(a,b),q=v.sq().sqrt();assert(q.sq()==v.sq());}mpz_clears(x,y,p,z,nullptr);
    }
    puts("Arithmetic self-check passed");
}
int main(int argc,char** argv){
    test_fp();std::ifstream in("work/params.txt");int count;in>>count;for(int i=0;i<count;++i){int l,x,y;std::string k;in>>l>>x>>y>>k;terms[l].push_back({x,y,Fp::read(k.c_str())});}
    std::string salt_hex;in>>salt_hex;unsigned char salt[32];for(int i=0;i<32;++i){unsigned x;sscanf(salt_hex.c_str()+2*i,"%2x",&x);salt[i]=x;}
    std::string checkpoint_path=argc>2?argv[2]:"work/fast-checkpoint.txt";
    U start=0,limit=argc>1?strtoull(argv[1],nullptr,10):1048576;Fq j(1728);std::ifstream checkpoint(checkpoint_path);if(checkpoint){std::string a,b;checkpoint>>start>>a>>b;j=Fq(Fp::read(a.c_str()),Fp::read(b.c_str()));}
    auto begin=std::chrono::steady_clock::now();int ls[4]={2,3,5,7};Fq previous;int previous_l=0;
    for(U i=start;i<limit;++i){unsigned char input[104],h[32];memcpy(input,j.a.v,32);memcpy(input+32,j.b.v,32);for(int k=0;k<8;++k)input[64+k]=i>>(56-8*k);memcpy(input+72,salt,32);SHA256(input,sizeof(input),h);int ell=ls[h[0]%4];auto r=get_roots(j,ell,ell==previous_l?&previous:nullptr);previous=j;previous_l=ell;j=r[h[1]%r.size()];
        if((i+1)%1000==0||i+1==limit){double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();printf("%llu %s %s %.3f\n",i+1,j.a.str().c_str(),j.b.str().c_str(),sec);fflush(stdout);std::ofstream out(checkpoint_path+".tmp");out<<i+1<<" "<<j.a.str()<<" "<<j.b.str()<<"\n";out.close();rename((checkpoint_path+".tmp").c_str(),checkpoint_path.c_str());}
    }
}
