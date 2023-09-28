# -*- coding: utf-8 -*-
"""XGBRegressor(alpha=0.3391108329877409, base_score=0.5, booster='gbtree',
             callbacks=None, colsample_bylevel=1, colsample_bynode=0.9,
             colsample_bytree=0.9, early_stopping_rounds=None,
             enable_categorical=False, eta=0.9452722646544713,
             eval_metric='mae', feature_types=None, gamma=0.011255353367418076,
             gpu_id=-1, grow_policy='depthwise', importance_type=None,
             interaction_constraints='', lambda=0.19373723699071155,
             learning_rate=0.945272267, max_bin=256, max_cat_threshold=64,
             max_cat_to_onehot=4, max_delta_step=0, max_depth=4, max_leaves=0,
             min_child_weight=7, missing=nan, monotone_constraints='()',
             n_estimators=30, n_jobs=0, ...)
Error: 0.047661"""
def features(ft, data):
		data[0] = (ft.get("length") - 136.6196185884635) / 100.86082059541495
		data[1] = (ft.get("speed") - 13.986934871911906) / 4.71750654884318
		data[2] = (ft.get("num_lanes") - 1.2681719632566897) / 0.6868784909822384
		data[3] = ft.get("change_speed")
		data[4] = ft.get("change_num_lanes")
		data[5] = ft.get("num_to_links")
		data[6] = ft.get("junction_inc_lanes")
		data[7] = ft.get("priority_lower")
		data[8] = ft.get("priority_equal")
		data[9] = ft.get("priority_higher")
		data[10] = ft.get("is_secondary_or_higher")
		data[11] = ft.get("is_primary_or_higher")
		data[12] = ft.get("is_motorway")
		data[13] = ft.get("is_link")

params = [0.3608418, 0.34890103, 0.3805294, 0.367862, 0.3214511, 0.25815126, 0.3545712, 0.32907134, 0.3583316, 0.37464577, 0.2698579, 0.22336875, 0.07104687, 0.053362835, 0.041006442, 0.025985682, 0.016914705, 0.030068675, 0.02692251, 0.007944532, -0.057301573, -0.01079493, 0.024668941, 0.065943725, 0.0073271547, -0.010634697, -0.042568587, -0.005014392, 0.0064422577, -0.008124101, -0.0009762109, -0.021804716, -0.041783743, -0.019399365, -0.013127809, 0.010771646, -0.02702811, -0.0071091, -0.019728376, -8.590933e-06, 0.0075863185, -0.000997167, 0.005540737, -0.020661844, 0.070752524, -0.010993776, 0.0061843814, 0.04742048, 0.0, -0.04123083, 0.0020972916, 0.01982593, -0.016842471, 0.002185143, -0.010056106, 0.005740708, -0.0010336025, -0.008926538, 0.0066137724, -0.055676598, -0.04465999, 0.011639535, 0.023085762, 0.0429667, -0.0047127116, 0.0066190767, -0.01991489, 0.012343046, -0.00030098224, 0.03327441, -0.02933379, 0.00227875, 0.013856811, -0.002690753, 0.0011580876, 0.009282305, -0.0032510154, 0.0037855355, 0.016429743, -0.0069674533, -0.0029329038, -0.016298464, -0.0022534884, 0.012884261, 0.0053116493, 0.021705957, -0.0211505, -0.0044319867, 0.005657457, -0.012777755, 0.0024879414, -0.016855681, -0.0006641551, -0.03385302, -0.039455965, -0.008037433, 0.054003634, 0.0, 0.00022664567, -0.007361894, -0.00042022497, 0.002072075, -0.02629097, -0.0057141623, 0.0, 0.02430369, 0.008704219, 0.00015066605, 0.029546643, 0.00025354454, -0.001516591, -0.031973023, -0.011100723, -0.0027563435, 0.009762235, 0.05289628, -0.038872607, 0.0, 0.011091023, -0.0006365045, -0.00012944487, 0.026204467, 0.0, 0.016556863, 0.0, -0.018513616, 0.019378055, 0.021001568, -0.021603102, 0.00015185689, -0.003958503, 0.013025162, -0.029794283, -0.02102098, -0.0009905503, 0.0024388963, -0.018523036, -0.0026774986, 0.02191896, 0.040357094, 0.0007669913, 0.0, 0.030865172, 0.012599033, 0.001843638, 0.00020173307, -0.006769137, -0.00031856322, 0.021274647, -0.024304036, -0.0033816784, 0.057870377, 0.0, -0.025712753, 0.012415222, 2.5677633e-05, -0.003756883, 0.006571175, 0.0011496701, 0.000138112, -0.0034407757, -0.0058021317, -0.056079507, -0.00035336296, 0.017468143, 0.012312527, -0.0016519147, -0.047752056, -0.035473906, 0.0, -0.0015261818, 0.015923837, 0.015606506, 0.0, -0.054741237, 0.0, -0.0025508015, 0.0022049379, -0.058122016, -0.0013978699, -0.026567709, -0.00024357338, 0.013887028, -0.00023815365, -0.0035327831, 0.015097718, -0.008128642, 8.880287e-05, 0.0067553106, -0.039901286, -0.0010965111, -0.012228503, 0.0025326295, 0.009830933, -0.004871507, 0.0007961357, -0.001985299, -0.00078088214, -0.015130762, 0.026426077, -0.011166116, 0.0047168666, -0.027053688, 0.0, 0.02502007, 0.0014169022, 0.027513124, 0.0, -0.006609659, 0.0067208144, 0.0007307121, -0.0007767367, -0.008880603, -0.0024207279, 0.0018657955, 0.007664186, -0.009534747, 0.00017667886, 0.0024938702, 0.000160656, -0.016127694, 0.031065073, -0.04356924, 0.0, 0.012454214, 9.2470545e-05, 0.013130494, -0.008663621, 0.020356651, 0.007865714, -0.0008692618, 0.004226911, -0.04767229, -0.00800842, 0.022846434, -0.0005788225, 0.009330586, -0.0019520844, 0.014785738, -0.041578304, 0.005497856, -0.032945607, 0.0, 0.0, -0.0013004113, 0.014651219, 0.0021028256, -0.008371005, -0.025870936, 0.0024653892, -7.002424e-05, 0.005613593, -0.0016404922, 0.008008113, -0.07883139, -0.008216268, 3.8600334e-05, -0.017916556, 0.0024656826, -0.060181007, 0.00026912204, 0.031037448, -0.009628712, -0.0120592415, 0.012064624, 0.0031491993, 0.013506664, 0.07318686, 0.00520229, -0.015804362, 0.011408404, 0.011172467, -0.001980757, -0.0025338277, 0.04618932, 0.0, -0.036171604, -0.0072938483, -0.0045603677, 8.558682e-05, -0.0021300775, 0.0059226053, 0.0015338295, -0.008351804, -0.0120370975, 0.0016534014, -0.009641722, 0.0024682067, -0.005995545, 0.0012730533, 0.0062334156, -0.0021061848, 0.0030723317, -0.00076261914, -0.000409436, 0.0007906831, 0.0, -0.061738558, -0.003120113, 0.028220955, 0.0022685728, -0.078828804, -0.0061356295, 8.381979e-05, 0.009887914, -0.00015392517, 0.008531038, 0.014667562, -0.01351278, 0.032202978, -0.02082266, 0.010006648, -0.03738514, 0.018855287, -0.058886614, -0.002497527, 0.0, 0.0059951753, 0.004368303, -0.0039021652, 0.0, -0.024193443, 0.0037743084, -0.0009127918, 0.0060951156, -0.0035422945, -0.00077070843, 0.001098186, 0.045046873, 0.0, 0.018084358, 0.0, 0.0, 0.011261725, -0.01039281, -0.0030560154, 0.016621474, 0.0, 0.007005952, 0.00014934929, -0.0041960427, -0.04577778, -0.001939774, 0.0002733276, 0.00912787, 0.004038844, -0.004946535, -0.026469113, 0.0, -0.0036243391, -3.5375142e-05, -0.0047778115, 0.014300297, 0.0039307415, 0.0, 0.0023882187, 0.00014195738, 0.011001494, 0.0011960509, 4.1772782e-05, -0.059463408, 0.0, 0.025786124, 0.0, -0.03289172, 0.003945976, -0.020250496, -6.1883075e-05, 0.009469738, -0.0036501247, 0.019228429, -0.005557274, 9.671706e-05, -0.0074998294, 0.02349894, 0.0018955221, 0.00071145897, -0.02839732, 0.0, -5.2149077e-05, -0.04872126, 0.022880139, 0.0, -0.017270446, 0.010601865, -0.00931396, 0.037245013, 0.0, 0.01629717, 0.0, -0.019269185, 0.014912463, 0.00050286605, -0.00011430594, 0.0055607953, -0.0004733346, 0.0, -0.018639635, 0.0, -0.013346717, 0.028006427, 0.004957935, 0.0, -0.018996669, -0.0012800392, 0.019457394]
def score(params, inputs):
    if inputs[0] >= -0.18931651:
        if inputs[3] >= -5.5550003:
            if inputs[5] >= 1.5:
                if inputs[9] >= 0.5:
                    var0 = params[0]
                else:
                    var0 = params[1]
            else:
                if inputs[11] >= 0.5:
                    var0 = params[2]
                else:
                    var0 = params[3]
        else:
            if inputs[3] >= -12.775:
                var0 = params[4]
            else:
                var0 = params[5]
    else:
        if inputs[3] >= -4.165:
            if inputs[1] >= -0.31519508:
                if inputs[11] >= 0.5:
                    var0 = params[6]
                else:
                    var0 = params[7]
            else:
                if inputs[6] >= 2.5:
                    var0 = params[8]
                else:
                    var0 = params[9]
        else:
            if inputs[0] >= -0.72341883:
                var0 = params[10]
            else:
                var0 = params[11]
    if inputs[0] >= -1.1267469:
        if inputs[2] >= 0.3375095:
            if inputs[0] >= 1.1064789:
                if inputs[12] >= 0.5:
                    var1 = params[12]
                else:
                    var1 = params[13]
            else:
                if inputs[4] >= -0.5:
                    var1 = params[14]
                else:
                    var1 = params[15]
        else:
            if inputs[9] >= 0.5:
                if inputs[0] >= -0.18297113:
                    var1 = params[16]
                else:
                    var1 = params[17]
            else:
                if inputs[3] >= 1.385:
                    var1 = params[18]
                else:
                    var1 = params[19]
    else:
        if inputs[2] >= 0.3375095:
            if inputs[0] >= -1.1286306:
                var1 = params[20]
            else:
                if inputs[5] >= 1.5:
                    var1 = params[21]
                else:
                    var1 = params[22]
        else:
            if inputs[3] >= 12.5:
                var1 = params[23]
            else:
                if inputs[9] >= 0.5:
                    var1 = params[24]
                else:
                    var1 = params[25]
    if inputs[5] >= 2.5:
        if inputs[0] >= -0.6054345:
            if inputs[1] >= -0.60984224:
                if inputs[7] >= 0.5:
                    var2 = params[26]
                else:
                    var2 = params[27]
            else:
                if inputs[0] >= -0.37278715:
                    var2 = params[28]
                else:
                    var2 = params[29]
        else:
            if inputs[9] >= 0.5:
                if inputs[0] >= -0.7754212:
                    var2 = params[30]
                else:
                    var2 = params[31]
            else:
                if inputs[1] >= -0.60984224:
                    var2 = params[32]
                else:
                    var2 = params[33]
    else:
        if inputs[1] >= 0.8623338:
            if inputs[4] >= 0.5:
                if inputs[4] >= 1.5:
                    var2 = params[34]
                else:
                    var2 = params[35]
            else:
                if inputs[1] >= 3.5120387:
                    var2 = params[36]
                else:
                    var2 = params[37]
        else:
            if inputs[7] >= 0.5:
                if inputs[1] >= -0.9044894:
                    var2 = params[38]
                else:
                    var2 = params[39]
            else:
                if inputs[0] >= -0.82038414:
                    var2 = params[40]
                else:
                    var2 = params[41]
    if inputs[12] >= 0.5:
        if inputs[1] >= 3.5120387:
            if inputs[0] >= -0.58545643:
                if inputs[0] >= 0.43689296:
                    var3 = params[42]
                else:
                    var3 = params[43]
            else:
                if inputs[0] >= -1.1621423:
                    var3 = params[44]
                else:
                    var3 = params[45]
        else:
            if inputs[0] >= 1.1714696:
                var3 = params[46]
            else:
                if inputs[2] >= 0.3375095:
                    var3 = params[47]
                else:
                    var3 = params[48]
    else:
        if inputs[13] >= 0.5:
            if inputs[6] >= 2.5:
                if inputs[9] >= 0.5:
                    var3 = params[49]
                else:
                    var3 = params[50]
            else:
                if inputs[0] >= -1.049363:
                    var3 = params[51]
                else:
                    var3 = params[52]
        else:
            if inputs[11] >= 0.5:
                if inputs[2] >= 1.7933712:
                    var3 = params[53]
                else:
                    var3 = params[54]
            else:
                if inputs[0] >= 0.7997692:
                    var3 = params[55]
                else:
                    var3 = params[56]
    if inputs[3] >= 5.835:
        if inputs[0] >= -0.21107918:
            if inputs[0] >= 0.64663744:
                var4 = params[57]
            else:
                if inputs[0] >= -0.20285001:
                    var4 = params[58]
                else:
                    var4 = params[59]
        else:
            if inputs[5] >= 1.5:
                if inputs[1] >= -0.60984224:
                    var4 = params[60]
                else:
                    var4 = params[61]
            else:
                if inputs[0] >= -0.68727994:
                    var4 = params[62]
                else:
                    var4 = params[63]
    else:
        if inputs[4] >= 0.5:
            if inputs[0] >= -0.15991956:
                if inputs[8] >= 0.5:
                    var4 = params[64]
                else:
                    var4 = params[65]
            else:
                if inputs[7] >= 0.5:
                    var4 = params[66]
                else:
                    var4 = params[67]
        else:
            if inputs[6] >= 1.5:
                if inputs[0] >= -1.2913301:
                    var4 = params[68]
                else:
                    var4 = params[69]
            else:
                if inputs[1] >= -0.31519508:
                    var4 = params[70]
                else:
                    var4 = params[71]
    if inputs[5] >= 1.5:
        if inputs[0] >= 0.17985559:
            if inputs[9] >= 0.5:
                if inputs[2] >= 0.3375095:
                    var5 = params[72]
                else:
                    var5 = params[73]
            else:
                if inputs[3] >= 2.775:
                    var5 = params[74]
                else:
                    var5 = params[75]
        else:
            if inputs[9] >= 0.5:
                if inputs[10] >= 0.5:
                    var5 = params[76]
                else:
                    var5 = params[77]
            else:
                if inputs[1] >= 1.4505682:
                    var5 = params[78]
                else:
                    var5 = params[79]
    else:
        if inputs[0] >= -0.1899114:
            if inputs[6] >= 1.5:
                if inputs[4] >= -0.5:
                    var5 = params[80]
                else:
                    var5 = params[81]
            else:
                if inputs[1] >= 2.3345098:
                    var5 = params[82]
                else:
                    var5 = params[83]
        else:
            if inputs[5] >= 0.5:
                if inputs[6] >= 1.5:
                    var5 = params[84]
                else:
                    var5 = params[85]
            else:
                if inputs[1] >= -0.60984224:
                    var5 = params[86]
                else:
                    var5 = params[87]
    if inputs[1] >= 0.8623338:
        if inputs[0] >= -0.49880242:
            if inputs[10] >= 0.5:
                if inputs[11] >= 0.5:
                    var6 = params[88]
                else:
                    var6 = params[89]
            else:
                if inputs[0] >= 1.5952713:
                    var6 = params[90]
                else:
                    var6 = params[91]
        else:
            if inputs[5] >= 1.5:
                if inputs[0] >= -0.6634352:
                    var6 = params[92]
                else:
                    var6 = params[93]
            else:
                if inputs[0] >= -0.5407909:
                    var6 = params[94]
                else:
                    var6 = params[95]
    else:
        if inputs[11] >= 0.5:
            if inputs[7] >= 0.5:
                if inputs[0] >= -1.1048355:
                    var6 = params[96]
                else:
                    var6 = params[97]
            else:
                if inputs[0] >= -0.45141035:
                    var6 = params[98]
                else:
                    var6 = params[99]
        else:
            if inputs[0] >= -1.249639:
                if inputs[0] >= -0.18971309:
                    var6 = params[100]
                else:
                    var6 = params[101]
            else:
                if inputs[0] >= -1.2646598:
                    var6 = params[102]
                else:
                    var6 = params[103]
    if inputs[0] >= 2.4748993:
        if inputs[3] >= -5.5550003:
            if inputs[7] >= 0.5:
                if inputs[3] >= 1.39:
                    var7 = params[104]
                else:
                    var7 = params[105]
            else:
                if inputs[1] >= 1.4505682:
                    var7 = params[106]
                else:
                    var7 = params[107]
        else:
            var7 = params[108]
    else:
        if inputs[0] >= -1.1069176:
            if inputs[0] >= -1.0723155:
                if inputs[0] >= -0.58317614:
                    var7 = params[109]
                else:
                    var7 = params[110]
            else:
                if inputs[7] >= 0.5:
                    var7 = params[111]
                else:
                    var7 = params[112]
        else:
            if inputs[5] >= 0.5:
                if inputs[10] >= 0.5:
                    var7 = params[113]
                else:
                    var7 = params[114]
            else:
                var7 = params[115]
    if inputs[6] >= 5.5:
        if inputs[4] >= -0.5:
            if inputs[8] >= 0.5:
                if inputs[6] >= 6.5:
                    var8 = params[116]
                else:
                    var8 = params[117]
            else:
                if inputs[10] >= 0.5:
                    var8 = params[118]
                else:
                    var8 = params[119]
        else:
            if inputs[10] >= 0.5:
                if inputs[1] >= 0.8623338:
                    var8 = params[120]
                else:
                    var8 = params[121]
            else:
                var8 = params[122]
    else:
        if inputs[1] >= 3.5120387:
            if inputs[2] >= 3.2492328:
                if inputs[1] >= 4.747861:
                    var8 = params[123]
                else:
                    var8 = params[124]
            else:
                if inputs[3] >= -1.39:
                    var8 = params[125]
                else:
                    var8 = params[126]
        else:
            if inputs[4] >= 2.5:
                if inputs[8] >= 0.5:
                    var8 = params[127]
                else:
                    var8 = params[128]
            else:
                if inputs[3] >= -1.385:
                    var8 = params[129]
                else:
                    var8 = params[130]
    if inputs[5] >= 1.5:
        if inputs[1] >= -0.9044894:
            if inputs[3] >= 1.385:
                if inputs[2] >= 0.3375095:
                    var9 = params[131]
                else:
                    var9 = params[132]
            else:
                if inputs[4] >= 0.5:
                    var9 = params[133]
                else:
                    var9 = params[134]
        else:
            if inputs[3] >= 5.5550003:
                if inputs[0] >= -0.824697:
                    var9 = params[135]
                else:
                    var9 = params[136]
            else:
                if inputs[9] >= 0.5:
                    var9 = params[137]
                else:
                    var9 = params[138]
    else:
        if inputs[3] >= 1.385:
            if inputs[0] >= -0.8564735:
                if inputs[9] >= 0.5:
                    var9 = params[139]
                else:
                    var9 = params[140]
            else:
                if inputs[3] >= 8.335:
                    var9 = params[141]
                else:
                    var9 = params[142]
        else:
            if inputs[1] >= 1.4505682:
                if inputs[0] >= 2.2239594:
                    var9 = params[143]
                else:
                    var9 = params[144]
            else:
                if inputs[3] >= -1.385:
                    var9 = params[145]
                else:
                    var9 = params[146]
    if inputs[7] >= 0.5:
        if inputs[0] >= -0.90738523:
            if inputs[0] >= -0.103158176:
                if inputs[6] >= 2.5:
                    var10 = params[147]
                else:
                    var10 = params[148]
            else:
                if inputs[1] >= -0.9044894:
                    var10 = params[149]
                else:
                    var10 = params[150]
        else:
            if inputs[1] >= -0.60984224:
                if inputs[6] >= 2.5:
                    var10 = params[151]
                else:
                    var10 = params[152]
            else:
                if inputs[3] >= 5.5550003:
                    var10 = params[153]
                else:
                    var10 = params[154]
    else:
        if inputs[6] >= 2.5:
            if inputs[0] >= -0.19030797:
                if inputs[0] >= -0.02612133:
                    var10 = params[155]
                else:
                    var10 = params[156]
            else:
                if inputs[0] >= -0.41636205:
                    var10 = params[157]
                else:
                    var10 = params[158]
        else:
            if inputs[8] >= 0.5:
                if inputs[0] >= -0.8501281:
                    var10 = params[159]
                else:
                    var10 = params[160]
            else:
                if inputs[0] >= -1.0568982:
                    var10 = params[161]
                else:
                    var10 = params[162]
    if inputs[0] >= -0.8138405:
        if inputs[0] >= -0.8104695:
            if inputs[3] >= -5.5550003:
                if inputs[0] >= -0.80809:
                    var11 = params[163]
                else:
                    var11 = params[164]
            else:
                if inputs[0] >= 0.62140465:
                    var11 = params[165]
                else:
                    var11 = params[166]
        else:
            if inputs[2] >= 0.3375095:
                var11 = params[167]
            else:
                if inputs[0] >= -0.81126267:
                    var11 = params[168]
                else:
                    var11 = params[169]
    else:
        if inputs[5] >= 2.5:
            if inputs[9] >= 0.5:
                if inputs[1] >= -0.60984224:
                    var11 = params[170]
                else:
                    var11 = params[171]
            else:
                if inputs[0] >= -1.164026:
                    var11 = params[172]
                else:
                    var11 = params[173]
        else:
            if inputs[13] >= 0.5:
                if inputs[3] >= 2.775:
                    var11 = params[174]
                else:
                    var11 = params[175]
            else:
                if inputs[2] >= 0.3375095:
                    var11 = params[176]
                else:
                    var11 = params[177]
    if inputs[1] >= 5.042508:
        if inputs[5] >= 1.5:
            if inputs[0] >= 0.9575609:
                var12 = params[178]
            else:
                var12 = params[179]
        else:
            if inputs[0] >= 0.47868323:
                if inputs[4] >= -0.5:
                    var12 = params[180]
                else:
                    var12 = params[181]
            else:
                var12 = params[182]
    else:
        if inputs[6] >= 3.5:
            if inputs[0] >= -1.1479642:
                if inputs[5] >= 2.5:
                    var12 = params[183]
                else:
                    var12 = params[184]
            else:
                if inputs[4] >= -0.5:
                    var12 = params[185]
                else:
                    var12 = params[186]
        else:
            if inputs[0] >= -1.2884054:
                if inputs[4] >= -0.5:
                    var12 = params[187]
                else:
                    var12 = params[188]
            else:
                if inputs[5] >= 1.5:
                    var12 = params[189]
                else:
                    var12 = params[190]
    if inputs[3] >= -5.835:
        if inputs[6] >= 4.5:
            if inputs[0] >= -0.2966922:
                if inputs[8] >= 0.5:
                    var13 = params[191]
                else:
                    var13 = params[192]
            else:
                if inputs[10] >= 0.5:
                    var13 = params[193]
                else:
                    var13 = params[194]
        else:
            if inputs[0] >= -0.5833248:
                if inputs[1] >= -0.9044894:
                    var13 = params[195]
                else:
                    var13 = params[196]
            else:
                if inputs[5] >= 0.5:
                    var13 = params[197]
                else:
                    var13 = params[198]
    else:
        if inputs[7] >= 0.5:
            var13 = params[199]
        else:
            if inputs[0] >= 0.71465194:
                if inputs[0] >= 2.5458884:
                    var13 = params[200]
                else:
                    var13 = params[201]
            else:
                if inputs[0] >= -0.6475718:
                    var13 = params[202]
                else:
                    var13 = params[203]
    if inputs[3] >= 2.775:
        if inputs[9] >= 0.5:
            if inputs[0] >= -0.8122046:
                if inputs[3] >= 6.9449997:
                    var14 = params[204]
                else:
                    var14 = params[205]
            else:
                var14 = params[206]
        else:
            if inputs[0] >= 1.137264:
                if inputs[0] >= 2.1696272:
                    var14 = params[207]
                else:
                    var14 = params[208]
            else:
                if inputs[10] >= 0.5:
                    var14 = params[209]
                else:
                    var14 = params[210]
    else:
        if inputs[10] >= 0.5:
            if inputs[5] >= 1.5:
                if inputs[0] >= -0.79936504:
                    var14 = params[211]
                else:
                    var14 = params[212]
            else:
                if inputs[0] >= -0.27433467:
                    var14 = params[213]
                else:
                    var14 = params[214]
        else:
            if inputs[2] >= 0.3375095:
                if inputs[2] >= 1.7933712:
                    var14 = params[215]
                else:
                    var14 = params[216]
            else:
                if inputs[0] >= -0.8309928:
                    var14 = params[217]
                else:
                    var14 = params[218]
    if inputs[0] >= -1.2908344:
        if inputs[0] >= -1.2877609:
            if inputs[0] >= -1.2833984:
                if inputs[0] >= -1.2753179:
                    var15 = params[219]
                else:
                    var15 = params[220]
            else:
                var15 = params[221]
        else:
            if inputs[0] >= -1.2893472:
                var15 = params[222]
            else:
                var15 = params[223]
    else:
        var15 = params[224]
    if inputs[0] >= -0.943425:
        if inputs[0] >= -0.89028245:
            if inputs[4] >= -1.5:
                var16 = params[225]
            else:
                if inputs[2] >= 3.2492328:
                    var16 = params[226]
                else:
                    var16 = params[227]
        else:
            if inputs[3] >= 6.9449997:
                var16 = params[228]
            else:
                if inputs[0] >= -0.92052215:
                    var16 = params[229]
                else:
                    var16 = params[230]
    else:
        if inputs[0] >= -0.9524473:
            if inputs[1] >= 0.27409926:
                var16 = params[231]
            else:
                if inputs[2] >= 0.3375095:
                    var16 = params[232]
                else:
                    var16 = params[233]
        else:
            if inputs[4] >= 0.5:
                if inputs[1] >= 0.27409926:
                    var16 = params[234]
                else:
                    var16 = params[235]
            else:
                if inputs[0] >= -0.9611722:
                    var16 = params[236]
                else:
                    var16 = params[237]
    if inputs[6] >= 7.5:
        if inputs[2] >= 3.2492328:
            if inputs[0] >= -0.7591116:
                var17 = params[238]
            else:
                if inputs[0] >= -0.8616787:
                    var17 = params[239]
                else:
                    var17 = params[240]
        else:
            if inputs[1] >= -0.60984224:
                if inputs[0] >= -0.79941463:
                    var17 = params[241]
                else:
                    var17 = params[242]
            else:
                var17 = params[243]
    else:
        if inputs[4] >= 1.5:
            if inputs[13] >= 0.5:
                if inputs[6] >= 3.5:
                    var17 = params[244]
                else:
                    var17 = params[245]
            else:
                if inputs[11] >= 0.5:
                    var17 = params[246]
                else:
                    var17 = params[247]
        else:
            if inputs[13] >= 0.5:
                if inputs[6] >= 2.5:
                    var17 = params[248]
                else:
                    var17 = params[249]
            else:
                if inputs[5] >= 0.5:
                    var17 = params[250]
                else:
                    var17 = params[251]
    if inputs[6] >= 1.5:
        if inputs[1] >= 0.8623338:
            if inputs[0] >= -0.96910393:
                if inputs[0] >= -0.7581202:
                    var18 = params[252]
                else:
                    var18 = params[253]
            else:
                if inputs[0] >= -0.97832453:
                    var18 = params[254]
                else:
                    var18 = params[255]
        else:
            if inputs[0] >= -1.0342927:
                if inputs[0] >= -1.030773:
                    var18 = params[256]
                else:
                    var18 = params[257]
            else:
                if inputs[4] >= -1.5:
                    var18 = params[258]
                else:
                    var18 = params[259]
    else:
        if inputs[0] >= -0.58600175:
            var18 = params[260]
        else:
            if inputs[13] >= 0.5:
                if inputs[4] >= 0.5:
                    var18 = params[261]
                else:
                    var18 = params[262]
            else:
                if inputs[0] >= -1.2735829:
                    var18 = params[263]
                else:
                    var18 = params[264]
    if inputs[1] >= 1.4505682:
        if inputs[2] >= 0.3375095:
            if inputs[10] >= 0.5:
                if inputs[6] >= 2.5:
                    var19 = params[265]
                else:
                    var19 = params[266]
            else:
                if inputs[2] >= 1.7933712:
                    var19 = params[267]
                else:
                    var19 = params[268]
        else:
            if inputs[5] >= 1.5:
                if inputs[6] >= 2.5:
                    var19 = params[269]
                else:
                    var19 = params[270]
            else:
                if inputs[6] >= 2.5:
                    var19 = params[271]
                else:
                    var19 = params[272]
    else:
        if inputs[1] >= 0.8623338:
            if inputs[0] >= -1.1637781:
                if inputs[0] >= -1.1464274:
                    var19 = params[273]
                else:
                    var19 = params[274]
            else:
                if inputs[2] >= 0.3375095:
                    var19 = params[275]
                else:
                    var19 = params[276]
        else:
            if inputs[3] >= 15.275:
                var19 = params[277]
            else:
                if inputs[2] >= 3.2492328:
                    var19 = params[278]
                else:
                    var19 = params[279]
    if inputs[2] >= 0.3375095:
        if inputs[0] >= -0.38770872:
            if inputs[4] >= -0.5:
                if inputs[2] >= 1.7933712:
                    var20 = params[280]
                else:
                    var20 = params[281]
            else:
                if inputs[2] >= 1.7933712:
                    var20 = params[282]
                else:
                    var20 = params[283]
        else:
            if inputs[4] >= 0.5:
                if inputs[0] >= -1.1215913:
                    var20 = params[284]
                else:
                    var20 = params[285]
            else:
                if inputs[7] >= 0.5:
                    var20 = params[286]
                else:
                    var20 = params[287]
    else:
        if inputs[11] >= 0.5:
            if inputs[8] >= 0.5:
                if inputs[0] >= -0.97723395:
                    var20 = params[288]
                else:
                    var20 = params[289]
            else:
                if inputs[0] >= -0.17330435:
                    var20 = params[290]
                else:
                    var20 = params[291]
        else:
            if inputs[0] >= 1.774677:
                if inputs[6] >= 2.5:
                    var20 = params[292]
                else:
                    var20 = params[293]
            else:
                if inputs[6] >= 2.5:
                    var20 = params[294]
                else:
                    var20 = params[295]
    if inputs[3] >= -11.385:
        if inputs[1] >= 2.3345098:
            if inputs[4] >= 2.5:
                if inputs[6] >= 4.5:
                    var21 = params[296]
                else:
                    var21 = params[297]
            else:
                if inputs[0] >= -1.0748932:
                    var21 = params[298]
                else:
                    var21 = params[299]
        else:
            if inputs[1] >= 0.27409926:
                if inputs[5] >= 0.5:
                    var21 = params[300]
                else:
                    var21 = params[301]
            else:
                if inputs[13] >= 0.5:
                    var21 = params[302]
                else:
                    var21 = params[303]
    else:
        var21 = params[304]
    if inputs[0] >= -1.2305534:
        if inputs[0] >= -1.2270832:
            if inputs[0] >= -1.2170694:
                if inputs[0] >= -1.2048744:
                    var22 = params[305]
                else:
                    var22 = params[306]
            else:
                if inputs[4] >= 0.5:
                    var22 = params[307]
                else:
                    var22 = params[308]
        else:
            var22 = params[309]
    else:
        if inputs[0] >= -1.2419057:
            if inputs[0] >= -1.2383859:
                if inputs[0] >= -1.2345688:
                    var22 = params[310]
                else:
                    var22 = params[311]
            else:
                var22 = params[312]
        else:
            if inputs[0] >= -1.2443843:
                var22 = params[313]
            else:
                if inputs[0] >= -1.2451775:
                    var22 = params[314]
                else:
                    var22 = params[315]
    if inputs[0] >= -0.23313928:
        if inputs[3] >= 5.5550003:
            if inputs[5] >= 1.5:
                if inputs[5] >= 2.5:
                    var23 = params[316]
                else:
                    var23 = params[317]
            else:
                if inputs[1] >= 0.8623338:
                    var23 = params[318]
                else:
                    var23 = params[319]
        else:
            if inputs[3] >= 4.165:
                if inputs[1] >= -0.60984224:
                    var23 = params[320]
                else:
                    var23 = params[321]
            else:
                if inputs[13] >= 0.5:
                    var23 = params[322]
                else:
                    var23 = params[323]
    else:
        if inputs[3] >= -4.165:
            if inputs[0] >= -0.29907173:
                if inputs[1] >= -0.9044894:
                    var23 = params[324]
                else:
                    var23 = params[325]
            else:
                if inputs[5] >= 1.5:
                    var23 = params[326]
                else:
                    var23 = params[327]
        else:
            if inputs[11] >= 0.5:
                if inputs[3] >= -5.835:
                    var23 = params[328]
                else:
                    var23 = params[329]
            else:
                if inputs[3] >= -5.5550003:
                    var23 = params[330]
                else:
                    var23 = params[331]
    if inputs[4] >= 1.5:
        if inputs[6] >= 2.5:
            if inputs[3] >= 8.335:
                var24 = params[332]
            else:
                if inputs[3] >= -4.165:
                    var24 = params[333]
                else:
                    var24 = params[334]
        else:
            var24 = params[335]
    else:
        if inputs[5] >= 1.5:
            if inputs[13] >= 0.5:
                if inputs[8] >= 0.5:
                    var24 = params[336]
                else:
                    var24 = params[337]
            else:
                if inputs[3] >= 6.8:
                    var24 = params[338]
                else:
                    var24 = params[339]
        else:
            if inputs[13] >= 0.5:
                if inputs[5] >= 0.5:
                    var24 = params[340]
                else:
                    var24 = params[341]
            else:
                if inputs[11] >= 0.5:
                    var24 = params[342]
                else:
                    var24 = params[343]
    if inputs[3] >= 5.5550003:
        if inputs[4] >= 0.5:
            if inputs[5] >= 1.5:
                var25 = params[344]
            else:
                if inputs[3] >= 16.945:
                    var25 = params[345]
                else:
                    var25 = params[346]
        else:
            if inputs[13] >= 0.5:
                if inputs[1] >= -0.9044894:
                    var25 = params[347]
                else:
                    var25 = params[348]
            else:
                if inputs[7] >= 0.5:
                    var25 = params[349]
                else:
                    var25 = params[350]
    else:
        if inputs[8] >= 0.5:
            if inputs[5] >= 2.5:
                if inputs[3] >= -1.39:
                    var25 = params[351]
                else:
                    var25 = params[352]
            else:
                if inputs[3] >= 1.385:
                    var25 = params[353]
                else:
                    var25 = params[354]
        else:
            if inputs[5] >= 1.5:
                if inputs[5] >= 2.5:
                    var25 = params[355]
                else:
                    var25 = params[356]
            else:
                if inputs[7] >= 0.5:
                    var25 = params[357]
                else:
                    var25 = params[358]
    if inputs[0] >= -1.0577409:
        if inputs[0] >= -1.0321611:
            if inputs[0] >= -1.031368:
                var26 = params[359]
            else:
                if inputs[10] >= 0.5:
                    var26 = params[360]
                else:
                    var26 = params[361]
        else:
            if inputs[0] >= -1.0363252:
                if inputs[10] >= 0.5:
                    var26 = params[362]
                else:
                    var26 = params[363]
            else:
                if inputs[0] >= -1.0379117:
                    var26 = params[364]
                else:
                    var26 = params[365]
    else:
        if inputs[0] >= -1.0630949:
            var26 = params[366]
        else:
            if inputs[9] >= 0.5:
                if inputs[0] >= -1.1243675:
                    var26 = params[367]
                else:
                    var26 = params[368]
            else:
                if inputs[5] >= 0.5:
                    var26 = params[369]
                else:
                    var26 = params[370]
    if inputs[0] >= 3.4985871:
        var27 = params[371]
    else:
        if inputs[0] >= -1.2877609:
            if inputs[0] >= -1.2194489:
                if inputs[0] >= -1.1886144:
                    var27 = params[372]
                else:
                    var27 = params[373]
            else:
                if inputs[0] >= -1.2219276:
                    var27 = params[374]
                else:
                    var27 = params[375]
        else:
            if inputs[10] >= 0.5:
                var27 = params[376]
            else:
                if inputs[6] >= 1.5:
                    var27 = params[377]
                else:
                    var27 = params[378]
    if inputs[0] >= -0.98506653:
        if inputs[0] >= -0.97316897:
            if inputs[0] >= -0.9722271:
                if inputs[0] >= -0.9719792:
                    var28 = params[379]
                else:
                    var28 = params[380]
            else:
                var28 = params[381]
        else:
            if inputs[0] >= -0.9796135:
                if inputs[4] >= 0.5:
                    var28 = params[382]
                else:
                    var28 = params[383]
            else:
                if inputs[0] >= -0.9821913:
                    var28 = params[384]
                else:
                    var28 = params[385]
    else:
        if inputs[0] >= -0.9951795:
            if inputs[0] >= -0.9861572:
                var28 = params[386]
            else:
                if inputs[0] >= -0.9890324:
                    var28 = params[387]
                else:
                    var28 = params[388]
        else:
            if inputs[0] >= -1.0013762:
                if inputs[3] >= 1.39:
                    var28 = params[389]
                else:
                    var28 = params[390]
            else:
                if inputs[6] >= 5.5:
                    var28 = params[391]
                else:
                    var28 = params[392]
    if inputs[0] >= -1.1534669:
        if inputs[0] >= -1.1388428:
            if inputs[0] >= -1.0633923:
                var29 = params[393]
            else:
                if inputs[0] >= -1.0981431:
                    var29 = params[394]
                else:
                    var29 = params[395]
        else:
            if inputs[1] >= 0.27409926:
                var29 = params[396]
            else:
                if inputs[1] >= -0.60984224:
                    var29 = params[397]
                else:
                    var29 = params[398]
    else:
        if inputs[0] >= -1.1652157:
            if inputs[1] >= 0.8623338:
                var29 = params[399]
            else:
                if inputs[6] >= 2.5:
                    var29 = params[400]
                else:
                    var29 = params[401]
        else:
            if inputs[6] >= 2.5:
                if inputs[1] >= -0.60984224:
                    var29 = params[402]
                else:
                    var29 = params[403]
            else:
                if inputs[1] >= -0.9044894:
                    var29 = params[404]
                else:
                    var29 = params[405]
    return 0.5 + (var0 + var1 + var2 + var3 + var4 + var5 + var6 + var7 + var8 + var9 + var10 + var11 + var12 + var13 + var14 + var15 + var16 + var17 + var18 + var19 + var20 + var21 + var22 + var23 + var24 + var25 + var26 + var27 + var28 + var29)

def batch_loss(params, inputs, targets):
    error = 0
    for x, y in zip(inputs, targets):
        preds = score(params, x)
        error += (preds - y) ** 2
    return error
