import json, base64, os
from datetime import date
import numpy as np, pandas as pd, plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Cu-AAS Digital Lab", page_icon="🧪", layout="wide")
CU, TEAL = "#B87333", "#0F3D3E"
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
html,body,[class*="css"]{{font-family:'Plus Jakarta Sans',sans-serif}}
.block-container{{padding-top:1.2rem;max-width:1250px}}
.hero{{background:linear-gradient(120deg,{TEAL},#1d6663 60%,{CU});color:#fff;padding:2rem 2.2rem;border-radius:20px;margin-bottom:1rem}}
.hero h1{{margin:0;font-weight:800;font-size:2.1rem;color:#fff}} .hero p{{margin:.4rem 0 0;opacity:.9}}
.chip{{display:inline-block;background:rgba(255,255,255,.16);padding:.2rem .7rem;border-radius:99px;font-size:.78rem;margin:.6rem .3rem 0 0}}
.card{{background:#fff;border-radius:16px;padding:1rem 1.2rem;box-shadow:0 2px 14px rgba(15,61,62,.08);border-top:4px solid {CU}}}
.card .l{{font-size:.75rem;color:#5b706f;text-transform:uppercase;letter-spacing:.06em}}
.card .v{{font-size:1.65rem;font-weight:800;color:{TEAL}}} .card .s{{font-size:.8rem;color:#5b706f}}
.ok{{color:#1b7f4b;font-weight:700}} .bad{{color:#c0392b;font-weight:700}}
.stTabs [data-baseweb="tab"]{{font-weight:600;font-size:1rem}}
h2,h3{{color:{TEAL}}}
</style>""", unsafe_allow_html=True)

COMP = [
 dict(id="hcl", name="Hollow Cathode Lamp (Cu)", bobot=15, color="#c9a227", fungsi="Sumber sinar monokromatis khas Cu pada 324,8 nm."),
 dict(id="neb", name="Nebulizer", bobot=15, color="#4aa3a2", fungsi="Mengubah larutan sampel menjadi aerosol halus."),
 dict(id="spr", name="Spray / Mixing Chamber", bobot=10, color="#6c8ebf", fungsi="Mencampur aerosol dengan gas dan memilah tetesan besar."),
 dict(id="brn", name="Burner Head + Nyala", bobot=20, color="#d9622b", fungsi="Nyala udara-asetilen mengatomisasi Cu menjadi atom bebas."),
 dict(id="mono", name="Monokromator", bobot=15, color="#7d5ba6", fungsi="Memilih panjang gelombang analit dan menyingkirkan sinar lain."),
 dict(id="pmt", name="Detektor (PMT)", bobot=10, color="#2e86c1", fungsi="Mengubah intensitas sinar menjadi sinyal listrik."),
 dict(id="gas", name="Sistem Gas (Asetilen/Udara)", bobot=10, color="#8a8f98", fungsi="Mengatur aliran bahan bakar dan oksidan secara stabil."),
 dict(id="out", name="Readout / Komputer", bobot=5, color="#34495e", fungsi="Menampilkan absorban dan mengolah data pengukuran."),
]

VIEWER = """<style>
body{margin:0;font-family:'Plus Jakarta Sans',Arial,sans-serif}
#w{display:flex;height:610px;border-radius:18px;overflow:hidden;background:#0c2a2b}
#c{flex:1;position:relative}
#p{width:310px;background:#fff;padding:14px;overflow:auto;box-sizing:border-box}
.it{padding:8px 10px;border-radius:10px;cursor:pointer;margin-bottom:5px;border:1px solid #e5eae9;font-size:13px}
.it:hover{background:#f1f6f5}.it.a{background:#0F3D3E;color:#fff}
.bar{height:5px;border-radius:9px;background:#B87333;margin-top:5px}
#inf{background:#F6F4EF;border-radius:12px;padding:10px;font-size:13px;margin-bottom:10px;min-height:80px;color:#12302F}
.bt{position:absolute;top:10px;left:10px;display:flex;gap:6px}
.bt button{background:rgba(255,255,255,.15);color:#fff;border:0;padding:6px 12px;border-radius:99px;cursor:pointer;font-size:12px}
.bt button:hover{background:#B87333}
.hint{position:absolute;bottom:10px;left:12px;color:#9fc3c2;font-size:11px}
</style>
<div id="w"><div id="c"><div class="bt"><button id="b1">Auto-rotate</button><button id="b2">Terurai</button><button id="b3">Reset</button></div>
<div class="hint">Drag: putar &middot; Scroll: zoom &middot; Klik komponen untuk detail</div></div>
<div id="p"><div id="inf"><b>Flame AAS</b><br>Pilih komponen di daftar atau klik langsung pada model 3D.</div><div id="ls"></div></div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
const comps=__DATA__, glb="__GLB__", wrap=document.getElementById('c');
const scene=new THREE.Scene(), cam=new THREE.PerspectiveCamera(45,wrap.clientWidth/610,.1,100);
const home=[7,4.5,9]; cam.position.set(...home);
const r=new THREE.WebGLRenderer({antialias:true}); r.setClearColor(0x0c2a2b); r.setSize(wrap.clientWidth,610); r.setPixelRatio(devicePixelRatio); wrap.appendChild(r.domElement);
const ctl=new THREE.OrbitControls(cam,r.domElement); ctl.autoRotate=true; ctl.autoRotateSpeed=1.4; ctl.enableDamping=true; ctl.target.set(0,1,0);
scene.add(new THREE.HemisphereLight(0xffffff,0x334455,.95)); const dl=new THREE.DirectionalLight(0xffffff,.9); dl.position.set(5,9,6); scene.add(dl);
scene.add(new THREE.GridHelper(16,32,0x2a6a6a,0x174647));
const M={}, orig=new Map(); let sel=null, exp=false;
function add(id,geo,pos,rot){const c=comps.find(x=>x.id==id);const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:c.color,metalness:.35,roughness:.45}));m.position.set(...pos);if(rot)m.rotation.set(...rot);m.userData.id=id;scene.add(m);(M[id]=M[id]||[]).push(m);orig.set(m,m.position.clone());return m}
function cyl(rt,rb,h){return new THREE.CylinderGeometry(rt,rb,h,32)}
const H=Math.PI/2;
if(glb){const b=Uint8Array.from(atob(glb),c=>c.charCodeAt(0)).buffer;new THREE.GLTFLoader().parse(b,'',g=>{scene.add(g.scene);const bx=new THREE.Box3().setFromObject(g.scene),s=bx.getSize(new THREE.Vector3()).length();cam.position.set(s*.8,s*.5,s*.9);ctl.target.copy(bx.getCenter(new THREE.Vector3()))})}
else{
 const base=new THREE.Mesh(new THREE.BoxGeometry(10,.3,3.6),new THREE.MeshStandardMaterial({color:0xdfe6e5,roughness:.6}));base.position.y=-.15;scene.add(base);
 add("hcl",cyl(.35,.35,1.4),[-4,1.5,0],[0,0,H]);
 add("neb",cyl(.14,.14,1),[-2.3,.75,0],[0,0,H]);
 add("spr",cyl(.5,.5,1.1),[-1.3,.55,0]);
 add("brn",new THREE.BoxGeometry(1.5,.25,.35),[-1.3,1.25,0]);
 const fl=add("brn",new THREE.ConeGeometry(.28,.8,24),[-1.3,1.8,0]);fl.material.color.set(0xff7a1a);fl.material.emissive.set(0x993300);
 add("mono",new THREE.BoxGeometry(2.2,1.7,1.4),[1.3,.85,0]);
 add("pmt",cyl(.4,.4,1.2),[3.4,1.5,0],[0,0,H]);
 add("gas",cyl(.35,.35,1.5),[-1.3,.75,-1.4]);
 add("out",new THREE.BoxGeometry(1.5,1,.12),[2.4,1.2,1.5],[0,-.3,0]);
 const beam=new THREE.Mesh(cyl(.03,.03,7.4),new THREE.MeshBasicMaterial({color:0xffe27a}));beam.rotation.z=H;beam.position.set(-.3,1.5,0);scene.add(beam);
}
const ls=document.getElementById('ls'),inf=document.getElementById('inf');
comps.forEach(c=>{const d=document.createElement('div');d.className='it';d.id='i_'+c.id;d.innerHTML=`<b>${c.name}</b><div style="opacity:.75;font-size:11px">Bobot ${c.bobot}%</div><div class="bar" style="width:${c.bobot*4.5}%"></div>`;d.onclick=()=>pick(c.id);ls.appendChild(d)});
function pick(id){sel=id;document.querySelectorAll('.it').forEach(e=>e.classList.toggle('a',e.id=='i_'+id));
 const c=comps.find(x=>x.id==id);inf.innerHTML=`<b style="color:#B87333">${c.name}</b><br>${c.fungsi}<br><b>Bobot: ${c.bobot}%</b>`;
 for(const k in M)M[k].forEach(m=>m.material.emissive.set(k==id?0x555555:(m.geometry.type=='ConeGeometry'?0x993300:0x000000)))}
const ray=new THREE.Raycaster(),mv=new THREE.Vector2();let dn=null;
r.domElement.onpointerdown=e=>dn=[e.clientX,e.clientY];
r.domElement.onpointerup=e=>{if(!dn||Math.hypot(e.clientX-dn[0],e.clientY-dn[1])>4)return;const R=r.domElement.getBoundingClientRect();
 mv.set((e.clientX-R.left)/R.width*2-1,-(e.clientY-R.top)/R.height*2+1);ray.setFromCamera(mv,cam);
 const h=ray.intersectObjects(Object.values(M).flat())[0];if(h)pick(h.object.userData.id)};
b1.onclick=()=>ctl.autoRotate=!ctl.autoRotate;
b2.onclick=()=>{exp=!exp};
b3.onclick=()=>{cam.position.set(...home);ctl.target.set(0,1,0);exp=false};
(function loop(){requestAnimationFrame(loop);orig.forEach((p,m)=>{const t=p.clone();if(exp)t.add(new THREE.Vector3(p.x*.5,(p.y>1?.8:0)+(p.z!=0?0:0),p.z*1.2));m.position.lerp(t,.12)});ctl.update();r.render(scene,cam)})();
</script>"""

def viewer():
    glb = ""
    if os.path.exists("model.glb"):
        glb = base64.b64encode(open("model.glb", "rb").read()).decode()
    components.html(VIEWER.replace("__DATA__", json.dumps(COMP)).replace("__GLB__", glb), height=630)

# ---------- perhitungan ----------
def uvol(v, tol, dT, alpha=0.00021):
    return float(np.sqrt((tol/np.sqrt(3))**2 + (v*dT*alpha/np.sqrt(3))**2))

def hitung(std, dis, tot, P):
    x, y = std.iloc[:, 0].astype(float).to_numpy(), std.iloc[:, 1].astype(float).to_numpy()
    n = len(x); b, a = np.polyfit(x, y, 1); r = float(np.corrcoef(x, y)[0, 1])
    ct = lambda A: (np.asarray(A, float) - a) / b
    Ad = dis.iloc[:, 0].dropna().astype(float).to_numpy(); ctd = ct(Ad); cd = ctd * P["fp1"]
    mean, sd = cd.mean(), cd.std(ddof=1); rsd = sd/mean*100
    At = tot.iloc[:, 0].dropna().astype(float).to_numpy(); ctt = ct(At) * P["fp2"]
    mt = ctt.mean(); rpd = (ctt.max()-ctt.min())/mt*100
    c2 = P["cstd"]*P["vstd"]/P["vsmp"]; c3 = float(ct(P["abs3"]))*P["fp3"]; rec = (c3-mt)/c2*100
    yc = a + b*x; sxy = np.sqrt(((y-yc)**2).sum()/(n-2)); sxx = ((x-x.mean())**2).sum()
    ureg = (sxy/b)*np.sqrt(1 + 1/n + (Ad.mean()-y.mean())**2/(b**2*sxx))
    ult, up5 = uvol(P["vlt"], P["tlt"], P["dT"]), uvol(P["vp"], P["tp"], P["dT"])
    ufp_rel = np.sqrt((ult/P["vlt"])**2 + (up5/P["vp"])**2); ufp = ufp_rel*P["fp1"]
    ctm = ctd.mean()
    comp = {"Regresi": ureg/ctm, "Faktor pengenceran": ufp_rel, "Labu takar": ult/P["vlt"],
            "Pipet": up5/P["vref"], "Presisi metode": sd/mean}
    uc = mean*np.sqrt(sum(v**2 for v in comp.values())); U = 2*uc
    return dict(x=x, y=y, a=a, b=b, r=r, Ad=Ad, ctd=ctd, cd=cd, mean=mean, sd=sd, rsd=rsd, ctt=ctt, mt=mt, rpd=rpd,
                c2=c2, c3=c3, rec=rec, ureg=ureg, ufp=ufp, comp=comp, uc=uc, U=U, Urel=U/mean*100, ctm=ctm)

# ---------- state / data ----------
st.session_state.setdefault("v", 0); v = st.session_state.v
st.sidebar.markdown("### ⚙️ Pengaturan")
with st.sidebar.expander("Batas keberterimaan (QC)", True):
    qr = st.number_input("r minimum", value=0.995, format="%.4f")
    qrsd = st.number_input("%RSD maksimum", value=5.0)
    qrpd = st.number_input("%RPD maksimum", value=5.0)
    qrec = st.slider("Rentang %Recovery", 50, 150, (80, 120))
with st.sidebar.expander("Parameter ketidakpastian"):
    vlt = st.number_input("Labu takar (mL)", value=50.0); tlt = st.number_input("Toleransi labu takar (±mL)", value=0.06)
    vp = st.number_input("Pipet FP (mL)", value=5.0); tp = st.number_input("Toleransi pipet FP (±mL)", value=0.015)
    vref = st.number_input("Volume pipet acuan (mL)", value=50.0)
    suhu = st.number_input("Suhu ruangan (°C)", value=27.5)
if st.sidebar.button("↺ Reset ke data contoh", use_container_width=True):
    st.session_state.v += 1; st.rerun()
st.sidebar.caption("Data contoh = data praktikum Kelompok 3.")

st.markdown("""<div class="hero"><h1>🧪 Cu-AAS Digital Lab</h1>
<p>Penetapan kadar logam Cu dalam sampel air secara Flame-AAS — dari data pengamatan hingga laporan, sepenuhnya digital.</p>
<span class="chip">Flame AAS</span><span class="chip">λ 324,8 nm</span><span class="chip">Kalibrasi linear</span><span class="chip">RSD · RPD · %Recovery</span><span class="chip">Ketidakpastian U95</span></div>""", unsafe_allow_html=True)

t0, t1, t2, t3 = st.tabs(["🔬 Instrumen 3D", "📝 Input Data", "📈 Hasil & Grafik", "📄 Laporan"])

with t0:
    st.subheader("Instrumen Flame AAS — model 360°")
    viewer()
    st.caption("Bobot = kontribusi relatif tiap komponen terhadap kinerja pengukuran (usulan; ubah di `COMP`).")

with t1:
    c1, c2_ = st.columns(2)
    with c1:
        st.markdown("##### 1. Deret standar")
        std = st.data_editor(pd.DataFrame({"Konsentrasi (mg/L)": [0., 1, 2, 3, 4, 5], "Absorban": [.0002, .1035, .1962, .2935, .3844, .4733]}),
                             num_rows="dynamic", use_container_width=True, key=f"s{v}")
        st.markdown("##### 3. Cu total (duplo)")
        tot = st.data_editor(pd.DataFrame({"Abs": [.0981, .0989]}), num_rows="dynamic", use_container_width=True, key=f"t{v}")
        fp2 = st.number_input("FP Cu total", value=1.0)
    with c2_:
        st.markdown("##### 2. Cu terlarut (ulangan)")
        dis = st.data_editor(pd.DataFrame({"Abs": [.3726, .376, .3574, .3639, .3698]}), num_rows="dynamic", use_container_width=True, key=f"d{v}")
        fp1 = st.number_input("FP Cu terlarut", value=10.0)
        st.markdown("##### 4–5. Akurasi (spike)")
        a1, a2, a3 = st.columns(3)
        cstd = a1.number_input("Konc. standar (mg/L)", value=100.0); vstd = a2.number_input("Vol. standar (mL)", value=0.5)
        vsmp = a3.number_input("Vol. sampel (mL)", value=50.0)
        abs3 = st.number_input("Absorban sampel + spike (C3)", value=0.2178, format="%.4f"); fp3 = st.number_input("FP spike", value=1.0)

try:
    R = hitung(std, dis, tot, dict(fp1=fp1, fp2=fp2, cstd=cstd, vstd=vstd, vsmp=vsmp, abs3=abs3, fp3=fp3, vlt=vlt, tlt=tlt,
                                   vp=vp, tp=tp, vref=vref, dT=suhu-20))
    ok = True
except Exception as e:
    ok = False

def badge(c, t): return f'<span class="{"ok" if c else "bad"}">{"✔" if c else "✖"} {t}</span>'
def card(l, vv, s=""): return f'<div class="card"><div class="l">{l}</div><div class="v">{vv}</div><div class="s">{s}</div></div>'

with t2:
    if not ok: st.error("Data belum lengkap/valid. Periksa tab Input Data.")
    else:
        k = st.columns(4)
        k[0].markdown(card("Cu terlarut", f"{R['mean']:.2f} mg/L", f"± {R['U']:.2f} (k=2)"), unsafe_allow_html=True)
        k[1].markdown(card("Presisi %RSD", f"{R['rsd']:.2f}%", badge(R['rsd'] <= qrsd, f"≤ {qrsd}%")), unsafe_allow_html=True)
        k[2].markdown(card("Cu total · %RPD", f"{R['mt']:.3f} mg/L", f"%RPD {R['rpd']:.2f} " + badge(R['rpd'] <= qrpd, f"≤ {qrpd}%")), unsafe_allow_html=True)
        k[3].markdown(card("Akurasi %Recovery", f"{R['rec']:.1f}%", badge(qrec[0] <= R['rec'] <= qrec[1], f"{qrec[0]}–{qrec[1]}%")), unsafe_allow_html=True)
        st.write("")
        g, tb = st.columns([3, 2])
        with g:
            xs = np.linspace(0, R['x'].max()*1.05, 50)
            fig = go.Figure()
            fig.add_scatter(x=R['x'], y=R['y'], mode="markers", name="Standar", marker=dict(size=11, color=TEAL))
            fig.add_scatter(x=xs, y=R['a']+R['b']*xs, mode="lines", name="Regresi", line=dict(color=CU, width=3))
            fig.add_scatter(x=R['ctd'], y=R['Ad'], mode="markers", name="Sampel", marker=dict(size=11, symbol="diamond", color="#d9622b"))
            fig.update_layout(title=f"Kurva Kalibrasi: y = {R['b']:.4f}x + {R['a']:.4f} (r = {R['r']:.5f})", xaxis_title="Konsentrasi (mg/L)",
                              yaxis_title="Absorban", template="simple_white", height=420, legend=dict(orientation="h", y=-.2))
            st.plotly_chart(fig, use_container_width=True)
        with tb:
            st.markdown("##### Cu terlarut")
            st.dataframe(pd.DataFrame({"Abs": R['Ad'], "Ct (mg/L)": R['ctd'], "Kadar (mg/L)": R['cd']}).round(4), use_container_width=True, hide_index=True)
            st.markdown(f"Rata-rata **{R['mean']:.3f}** · SD **{R['sd']:.3f}** · %RSD **{R['rsd']:.2f}**")
            st.markdown(badge(R['r'] >= qr, f"r = {R['r']:.5f} (≥ {qr})"), unsafe_allow_html=True)
        st.markdown("##### Kontribusi ketidakpastian relatif")
        cf = go.Figure(go.Bar(x=list(R['comp'].keys()), y=[v_**2/sum(w**2 for w in R['comp'].values())*100 for v_ in R['comp'].values()], marker_color=CU))
        cf.update_layout(template="simple_white", height=300, yaxis_title="Kontribusi (%)"); st.plotly_chart(cf, use_container_width=True)

with t3:
    if not ok: st.error("Data belum lengkap/valid.")
    else:
        tbl = lambda d: pd.DataFrame(d).round(4).to_html(index=False, border=0)
        html = f"""<html><head><meta charset="utf-8"><style>body{{font-family:Arial;max-width:820px;margin:auto;color:#12302F}}
h1{{color:{TEAL};border-bottom:3px solid {CU}}}h3{{color:{CU}}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccd;padding:5px 9px;text-align:center}}th{{background:{TEAL};color:#fff}}</style></head><body>
<h1>Laporan Penetapan Kadar Cu dalam Sampel Air (Flame-AAS)</h1><p>Kelompok 3 · {date.today():%d %B %Y}</p>
<h3>1. Kurva Kalibrasi</h3>{tbl({"Konsentrasi (mg/L)": R['x'], "Absorban": R['y']})}
<p>y = {R['b']:.5f}x + {R['a']:.5f}; r = {R['r']:.5f}</p>
<h3>2. Cu Terlarut</h3>{tbl({"Abs": R['Ad'], "Ct (mg/L)": R['ctd'], "FP": fp1, "Kadar (mg/L)": R['cd']})}
<p>Rata-rata {R['mean']:.3f} mg/L · SD {R['sd']:.3f} · <b>%RSD {R['rsd']:.2f}%</b></p>
<h3>3. Cu Total (duplo)</h3>{tbl({"Abs": At_ if (At_ := tot.iloc[:,0].dropna().astype(float).to_numpy()) is not None else 0, "Kadar (mg/L)": R['ctt']})}
<p>Rata-rata {R['mt']:.4f} mg/L · <b>%RPD {R['rpd']:.2f}%</b></p>
<h3>4. Akurasi</h3><p>C1 = {R['mt']:.4f}; C2 (spike) = {R['c2']:.4f}; C3 = {R['c3']:.4f} mg/L → <b>%Recovery = {R['rec']:.2f}%</b></p>
<h3>5. Estimasi Ketidakpastian</h3>{tbl({"Komponen": list(R['comp'].keys()), "µx/x": list(R['comp'].values())})}
<p>µc = {R['uc']:.4f} mg/L · U95 (k=2) = {R['U']:.4f} mg/L · ketidakpastian relatif {R['Urel']:.2f}%</p>
<h3>6. Pelaporan Hasil</h3><p style="font-size:1.2em"><b>Kadar Cu terlarut = {R['mean']:.2f} ± {R['U']:.2f} mg/L</b> (k=2, tingkat kepercayaan 95%)</p></body></html>"""
        st.components.v1.html(html, height=900, scrolling=True)
        st.download_button("⬇ Unduh laporan (HTML → cetak ke PDF)", html, "laporan_Cu_AAS.html", "text/html", type="primary")

