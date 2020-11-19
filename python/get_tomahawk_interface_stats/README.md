This script is designed to help provide visibility for Broadcom Tomahawk based QFX5200 systems to display the logical ASIC to Physical port mapping along with the associated pipeline each port is associated with. This association is important when monitoring drop performance with PFC/ECN or RoCEv2 as ingress headroom buffers are carved up across four separate processing pipes so providing visibility into both ingress and egress traffic paths and associated buffer pools is important.

This script also polls the low level logical port counters from within the Broadcom shell not accessible from the Junos CLI for 'DROP_PKT_ING' or 'ingress_hw_drops'  which are only present during ingress traffic congestion and active dropping. The presence of active counters here indicates lossless traffic is being dropped in the ingress pipeline as a result of insufficient headroom buffer allocation to absorb inflight traffic before either ECN or PFC has affected the inbound traffic volume(s).


    mbp:interface-stats $ ./get_interface_stats.py --host qfx5200-1 --user labuser --interval 10
    Password:
    Connecting to qfx5200-1...
    Connected!
    Date&Time(PST):2018-05-22 13:59:25.089413
    interface       logical pipe     description             InBPS      OutBPS     InError  OutError Admin/Oper    ingr_hw_drops
    ------------------------------------------------------------------------------------------------------------------------
    pfe-0/0/0       cpu0    0        None                    ----       ----       0        0        up/up
    pfh-0/0/0       cpu0             None                    ----       ----       0        0        up/up
    sxe-0/0/0       ge1     2        None                    0.00bps    0.00bps    0        0        up/up
    xe-0/0/0:0      xe36    1        None                    0.00bps    0.00bps    0        0        up/down
    xe-0/0/0:1      xe37    1        qfx5200-2 xe-0/1/1      0.00bps    0.00bps    0        0        up/down
    xe-0/0/0:2      xe38    1        None                    0.00bps    0.00bps    0        0        up/down
    xe-0/0/0:3      xe39    1        None                    0.00bps    0.00bps    0        0        up/down
    et-0/0/2        xe43    1        qfx5100-48t-3_et-0/0/50 312.00bps  0.00bps    0        0        up/up
    et-0/0/3        xe47    1        None                    2.09Kbps   1.60Kbps   0        0        up/up
    et-0/0/6:0      xe57    2        server1 eth3            0.00bps    2.30Kbps   0        0        up/up
    et-0/0/6:1      xe58    2        None                    0.00bps    0.00bps    0        0        up/down
    et-0/0/6:2      xe59    2        None                    0.00bps    0.00bps    0        0        up/down
    et-0/0/6:3      xe60    2        None                    0.00bps    0.00bps    0        0        up/down
    et-0/0/30       ce2     0        qfx5200-3 et-0/0/30     528.00bps  432.00bps  0        0        up/up
    et-0/0/31       ce3     0        qfx5200-4 et-0/0/31     2.74Kbps   528.00bps  0        0        up/up
    --- 17.9089789391 seconds ---
    Sleeping for 10.0sec...
    ^CCaught Ctrl-C. Exiting!
