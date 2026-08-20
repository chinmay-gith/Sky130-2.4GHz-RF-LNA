v {xschem version=3.4.4 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
N 420 -70 420 -30 {
lab=RF_OUT}
N 420 -30 480 -30 {
lab=RF_OUT}
N 480 -70 480 -30 {
lab=RF_OUT}
N 480 -30 540 -30 {
lab=RF_OUT}
N 540 -30 540 0 {
lab=RF_OUT}
N 420 30 420 70 {
lab=#net1}
N 330 0 380 0 {
lab=#net2}
N 380 -120 380 0 {
lab=#net2}
N 420 0 460 0 {
lab=GND}
N 380 -200 380 -180 {
lab=VBIAS}
N 700 -100 700 -70 {
lab=GND}
N 230 -90 230 0 {
lab=#net3}
N 230 -90 260 -90 {
lab=#net3}
N 260 -30 260 0 {
lab=#net4}
N 260 0 270 0 {
lab=#net4}
C {sky130_fd_pr/nfet_01v8.sym} 400 0 0 0 {name=M1 W=40 L=0.15 nf=4 mult=1 model=nfet_01v8}
C {devices/ind.sym} 420 -100 0 0 {name=Lload value=3n m=1}
C {devices/capa.sym} 480 -100 0 0 {name=Cload value=1.5p m=1}
C {devices/ind.sym} 420 100 0 0 {name=Ls value=0.5n m=1}
C {devices/ind.sym} 300 0 1 0 {name=Lg value=35n m=1}
C {devices/res.sym} 200 0 1 0 {name=Rs value=50 m=1}
C {devices/vsource.sym} 170 30 0 0 {name=V1 value="dc 0 ac 1"}
C {devices/res.sym} 380 -150 0 0 {name=Rbias value=10k m=1}
C {devices/res.sym} 540 30 0 0 {name=Rload value=1000 m=1}
C {devices/gnd.sym} 170 60 0 0 {name=l1 lab=GND}
C {devices/gnd.sym} 420 130 0 0 {name=l2 lab=GND}
C {devices/gnd.sym} 460 0 0 0 {name=l3 lab=GND}
C {devices/gnd.sym} 540 60 0 0 {name=l4 lab=GND}
C {devices/lab_pin.sym} 420 -130 0 0 {name=p1 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 480 -130 0 0 {name=p2 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 380 -180 0 0 {name=p3 sig_type=std_logic lab=VBIAS}
C {devices/vsource.sym} 380 -230 2 0 {name=VB value=0.9}
C {devices/gnd.sym} 380 -260 0 0 {name=l5 lab=GND}
C {devices/vsource.sym} 700 -130 0 0 {name=VDD1 value=1.8}
C {devices/gnd.sym} 700 -70 0 0 {name=l6 lab=GND}
C {devices/lab_pin.sym} 700 -160 0 0 {name=p4 sig_type=std_logic lab=VDD}
C {devices/opin.sym} 540 -30 0 0 {name=p5 lab=RF_OUT}
C {devices/code_shown.sym} 800 -1370 0 0 {name=s1 only_toplevel=false value="
* --- Sky130 LNA testbench directives ---
* Adjust this include path to match your local sky130 install:
.lib /home/azmuth/.volare/volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.tech/combined/sky130.lib.spice tt
.control
ac dec 50 100meg 10g
plot vdb(RF_OUT)
.endc
"}
C {capa.sym} 260 -60 0 0 {name=C1
m=1
value=1p
footprint=1206
device="ceramic capacitor"}
