proc get_gty_iobanks {} {
    return [get_iobanks -filter {BANK_TYPE == BT_MGT}]
}

set banks [get_gty_iobanks]
set pindef {}
foreach bank $banks {
    set bank_pins {}
    foreach pin_direction {T R} {
        foreach polarity {N P} {
            #MGTYTX[N/P]n_BANK
            set pl [list]
            foreach bit {0 1 2 3} {
                lappend pl [get_package_pins -filter "PIN_FUNC =~ MGTY${pin_direction}X${polarity}${bit}_${bank}"]
            }
            dict set bank_pins ${pin_direction}X${polarity} $pl
        }
    }

    foreach refclk_id {0 1} {
        set diffpin {}
        foreach polarity {N P} {
            #MGTREFCLK[0/1][N/P]_BANK
            dict set diffpin $polarity [get_package_pins -filter "PIN_FUNC =~ MGTREFCLK${refclk_id}${polarity}_${bank}"]
        }
        dict set bank_pins MGTREFCLK${refclk_id} ${diffpin}
    }
    dict set pindef GTY$bank $bank_pins
}

set fid [open gt_pins_[get_property PART [current_project]].json w]
puts $fid [bd::dict2json -ws $pindef]
close $fid
