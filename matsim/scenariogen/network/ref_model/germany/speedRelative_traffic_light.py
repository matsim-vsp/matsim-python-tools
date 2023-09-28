# -*- coding: utf-8 -*-
"""XGBRegressor(alpha=0.047001391102599516, base_score=0.5, booster='gbtree',
             callbacks=None, colsample_bylevel=1, colsample_bynode=0.9,
             colsample_bytree=0.9, early_stopping_rounds=None,
             enable_categorical=False, eta=0.3941368339308491,
             eval_metric='mae', feature_types=None, gamma=0.015204717741625653,
             gpu_id=-1, grow_policy='depthwise', importance_type=None,
             interaction_constraints='', lambda=0.06265617744974636,
             learning_rate=0.394136846, max_bin=256, max_cat_threshold=64,
             max_cat_to_onehot=4, max_delta_step=0, max_depth=4, max_leaves=0,
             min_child_weight=1, missing=nan, monotone_constraints='()',
             n_estimators=30, n_jobs=0, ...)
Error: 0.065839"""
def features(ft, data):
		data[0] = (ft.get("length") - 118.1870083102493) / 85.53737656584288
		data[1] = (ft.get("speed") - 13.07573990377606) / 2.714858934612079
		data[2] = (ft.get("num_lanes") - 1.898819069835253) / 0.9764526365080834
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

params = [0.06790623, 0.034632765, -0.011209435, 0.04577619, 0.0880185, 0.047057196, 0.10822878, 0.08355451, -0.0819455, -0.034643985, -0.027316023, -0.07005219, -0.007893718, 0.050933607, -0.050275955, -0.0057284646, 0.017012136, 0.043477625, -0.01993124, 0.011612414, -0.033527438, -0.062167246, -0.0042647053, -0.036844037, 0.010196017, 0.056714352, -0.025823936, 0.034707848, 0.0015412709, 0.01949823, 0.027255317, -0.03200495, -0.05468421, 0.0, 0.019082194, -0.010470612, -0.026849343, -0.13238138, 0.035029292, 0.01832633, -0.020596212, -0.04140348, -0.0043531493, 0.03936372, -0.06849704, -0.0009418421, 0.009460706, -0.008723757, 0.036718156, -0.044914506, 0.035381146, 0.02266762, -0.014656713, 0.027509872, -0.022450017, 0.009973883, 0.021223705, -0.013778199, -0.016864818, -0.03560116, -0.013142123, 0.01078481, 0.0034205264, -0.019221146, -0.053455953, -0.086902104, -0.0545471, -0.027562099, -0.014050962, 0.0066683814, -0.0009228036, 0.01587043, -0.023853047, -0.0002186747, 0.015491075, -0.01240522, -0.047347978, 0.031765904, -0.039147522, 0.008001228, -0.066487804, -0.031976275, -0.04089825, 0.0053946464, 0.01517929, -0.019650074, 0.0370233, -0.038363665, -0.06605387, -0.02930215, -0.0087859705, -0.024408419, -0.004786583, 0.016753469, 0.026538929, 0.0021821405, 0.017158577, 0.0077318633, 0.013361957, 0.002492773, 0.016783584, -0.008524774, -0.0071881786, -0.017453086, 0.03549861, -0.04956106, 0.00886389, -0.008774117, 0.0025088205, -0.002580323, -0.010493644, -0.04805658, -0.066898845, -0.015498039, 0.010330905, 0.0029518704, -0.043891404, -0.009994398, 0.036285102, 0.004521423, -0.0066570383, -0.01676263, 0.010302288, -0.060991153, -0.011717055, -0.050649498, 0.0, -0.01821129, 0.023557747, 0.007826897, -0.015035515, -0.006106305, -0.03755243, 0.0023724097, -0.005185496, 0.005094755, 0.065492965, 0.0019828319, 0.02029748, 0.014927406, -0.00010956537, 0.013305125, -0.009676593, -0.03953449, 0.012009435, 0.0, 0.052751556, -0.008745545, -0.034963988, 0.044285417, -0.012566226, 0.008154273, -0.0033447242, 0.006168181, -0.0029966286, 0.0060548233, 0.00039674135, -0.021450378, 0.039186753, -0.003896553, -0.018237207, 0.0052921646, 0.0022821582, 0.051311508, 0.08115114, 0.0138180675, 0.0, 0.053865634, -0.038993374, -0.009050318, 0.013135795, 0.0066654873, 0.0007622345, 0.047147546, 0.009399889, -0.02897284, -0.006884936, 0.00662854, -0.010828887, -0.0013556709, 0.009268267, -0.0024131185, 0.005239874, -0.0051272567, 0.08559939, -0.01375245, 0.040658217, 0.0140133, 0.047104117, -0.018700076, -0.06612628, 0.012063506, 0.0017672975, -0.0007462956, -0.014046012, -0.0072673075, -0.02431682, 0.0023534077, -0.008500829, 0.10719526, 0.004079055, -0.0053740633, -0.09862536, 0.0040577766, -0.049893934, 0.011684913, 0.01898168, -0.034786213, -0.0014466611, 0.0, 0.07370232, 0.04828216, 0.015566578, -0.010944348, 0.0013533304, -0.0031485711, 0.00040815855, 0.077660136, 0.0, 0.008733414, -0.03529251, -0.022965346, -0.0037971581, -0.00070111395, 0.003429289, 0.00087198295, -0.027258886, 0.036887784, -0.014568294, 0.05453901, 0.014291372, -0.025041157, -0.060959555, 0.0068763434, 0.09121028, 0.0006954265, 0.00038299375, -0.020050624, -0.0014860297, -0.018464416, 0.017304298, 0.0056287106, 0.00079059287, -0.0026184975, 0.02052197, 0.0027167753, 0.14830045, 0.05380311, 0.06719894, 0.011664438, 0.058087803, -0.042504944, 0.020543959, -0.0017126647, -0.021107348, -0.024503708, -0.0010299521, 0.00022382621, 0.09911475, 0.008810727, -0.030270861, -0.0036977471, 0.034903526, 0.04277103, -0.0016510044, 0.04814092, 0.0, -0.099094965, -0.008851885, -0.008267712, 0.0050739637, 0.018586261, -0.042596452, -0.0028918746, 0.020863501, -0.0314092, 0.0, -0.0016262544, 0.0062467703, -0.002645085, 0.0009108173, 0.00846314, 0.025383726, -0.013415105, 0.0023971228, -0.072558574, -0.0014006126, -0.0026091759, -0.00025234264, -0.008309074, -0.0022059528, 0.014517953, -0.006325167, 0.0023618157, -0.0007848198, 0.001425744, 0.04030019, -6.477191e-05, 0.11148067, 0.0016294338, -0.021962913, -0.036813963, 0.03363942, -0.0062452178, 0.012401687, -8.250797e-05, -0.0032123856, -0.05763109, -0.0036932572, -0.021652194, 0.03144192, 0.020936608, -0.013293991, 0.003570338, 0.004783369, -0.0015694727, -0.013244351, -0.027097417, 0.014033851, 0.05943601, 0.001303502, 0.0007681418, -0.013094218, 6.0819482e-05, -0.003216767, -0.03489369, -0.004310269, 0.078428924, -0.020854548, -0.040383656, -8.884911e-05, -0.010848852, -0.0033101991, 0.02270593, -0.0034757163, 0.02270174, -0.05760729, 0.012181459, -0.0073860073, 0.0014437418, 0.0016960505, 0.030603828, -0.0483842, 0.015619719, -0.0063001984, -0.0024699746, 0.035763524, -0.019962663, 0.0017212804, 0.029769387, 0.00061234157, 0.039824042, -0.0010563757, 0.08099293, 0.00394579, 0.012517526, -0.0005035828, 0.0047116997, 0.0005257211, -0.0033985288, -0.024204433, 0.026075657, -0.012003716, -0.0006758022, -0.0016981185, 0.00068652624, 0.043410677, -0.02996935, 0.004826302, -0.011975468, 0.0042384565, 0.0061476687, -0.024505187, 0.025222618, 0.013374519, -0.05868894, 0.0024167027, -7.5827935e-05, 0.013496813, 0.0, -0.043456644, -0.004089359, -0.017123394, 0.0029439353, -0.0055463156, -0.012465894, 2.672521e-05, 0.001222799, -0.016599808, -0.0024725378, -0.030502506, -0.00064433145, -0.0047695637, 0.0007970989, -0.05864099, -0.021104973, 0.0, 0.024772102, 0.0079932045, -0.008547953, 0.00088216783, -0.035597026, 0.09471237, 0.010676396, -0.034800455, 0.0108672995, -0.003780443, 0.0015160043, -0.0021869375, -0.02006114, -0.061431926, 0.07598046, 0.028308306, 0.002596565]
def score(params, inputs):
    if inputs[0] >= -0.1273947:
        if inputs[6] >= 6.5:
            if inputs[0] >= 0.6765813:
                if inputs[0] >= 1.1753106:
                    var0 = params[0]
                else:
                    var0 = params[1]
            else:
                if inputs[1] >= -1.2360642:
                    var0 = params[2]
                else:
                    var0 = params[3]
        else:
            if inputs[1] >= -1.2360642:
                if inputs[0] >= 1.2711751:
                    var0 = params[4]
                else:
                    var0 = params[5]
            else:
                if inputs[0] >= 0.64478236:
                    var0 = params[6]
                else:
                    var0 = params[7]
    else:
        if inputs[6] >= 6.5:
            if inputs[5] >= 2.5:
                if inputs[1] >= -0.72406703:
                    var0 = params[8]
                else:
                    var0 = params[9]
            else:
                if inputs[0] >= -0.7543136:
                    var0 = params[10]
                else:
                    var0 = params[11]
        else:
            if inputs[0] >= -0.6443032:
                if inputs[1] >= -1.2360642:
                    var0 = params[12]
                else:
                    var0 = params[13]
            else:
                if inputs[1] >= -0.72406703:
                    var0 = params[14]
                else:
                    var0 = params[15]
    if inputs[6] >= 4.5:
        if inputs[0] >= -0.24336739:
            if inputs[0] >= 0.5039667:
                if inputs[6] >= 8.5:
                    var1 = params[16]
                else:
                    var1 = params[17]
            else:
                if inputs[6] >= 8.5:
                    var1 = params[18]
                else:
                    var1 = params[19]
        else:
            if inputs[6] >= 8.5:
                if inputs[0] >= -0.49056926:
                    var1 = params[20]
                else:
                    var1 = params[21]
            else:
                if inputs[2] >= 0.6156785:
                    var1 = params[22]
                else:
                    var1 = params[23]
    else:
        if inputs[0] >= -0.4307124:
            if inputs[0] >= 0.2598629:
                if inputs[13] >= 0.5:
                    var1 = params[24]
                else:
                    var1 = params[25]
            else:
                if inputs[13] >= 0.5:
                    var1 = params[26]
                else:
                    var1 = params[27]
        else:
            if inputs[0] >= -0.8881732:
                if inputs[0] >= -0.83574:
                    var1 = params[28]
                else:
                    var1 = params[29]
            else:
                if inputs[2] >= 0.6156785:
                    var1 = params[30]
                else:
                    var1 = params[31]
    if inputs[0] >= -0.34355754:
        if inputs[6] >= 8.5:
            if inputs[1] >= 0.81192434:
                if inputs[0] >= -0.27352965:
                    var2 = params[32]
                else:
                    var2 = params[33]
            else:
                if inputs[0] >= 0.2842967:
                    var2 = params[34]
                else:
                    var2 = params[35]
        else:
            if inputs[1] >= 0.81192434:
                if inputs[3] >= -5.5550003:
                    var2 = params[36]
                else:
                    var2 = params[37]
            else:
                if inputs[0] >= 0.7530391:
                    var2 = params[38]
                else:
                    var2 = params[39]
    else:
        if inputs[6] >= 5.5:
            if inputs[1] >= -0.72406703:
                if inputs[0] >= -0.648395:
                    var2 = params[40]
                else:
                    var2 = params[41]
            else:
                if inputs[3] >= 2.78:
                    var2 = params[42]
                else:
                    var2 = params[43]
        else:
            if inputs[1] >= 0.81192434:
                if inputs[6] >= 2.5:
                    var2 = params[44]
                else:
                    var2 = params[45]
            else:
                if inputs[0] >= -0.723333:
                    var2 = params[46]
                else:
                    var2 = params[47]
    if inputs[0] >= 0.011608863:
        if inputs[0] >= 1.6133647:
            if inputs[3] >= 6.95:
                if inputs[0] >= 3.2881882:
                    var3 = params[48]
                else:
                    var3 = params[49]
            else:
                if inputs[0] >= 2.6381216:
                    var3 = params[50]
                else:
                    var3 = params[51]
        else:
            if inputs[3] >= 5.5550003:
                if inputs[3] >= 6.9449997:
                    var3 = params[52]
                else:
                    var3 = params[53]
            else:
                if inputs[3] >= 1.385:
                    var3 = params[54]
                else:
                    var3 = params[55]
    else:
        if inputs[5] >= 2.5:
            if inputs[3] >= 5.5550003:
                if inputs[0] >= -0.5320132:
                    var3 = params[56]
                else:
                    var3 = params[57]
            else:
                if inputs[0] >= -0.7692194:
                    var3 = params[58]
                else:
                    var3 = params[59]
        else:
            if inputs[0] >= -0.89366794:
                if inputs[7] >= 0.5:
                    var3 = params[60]
                else:
                    var3 = params[61]
            else:
                if inputs[4] >= 0.5:
                    var3 = params[62]
                else:
                    var3 = params[63]
    if inputs[1] >= -1.2360642:
        if inputs[1] >= 1.8340769:
            if inputs[5] >= 2.5:
                if inputs[11] >= 0.5:
                    var4 = params[64]
                else:
                    var4 = params[65]
            else:
                if inputs[8] >= 0.5:
                    var4 = params[66]
                else:
                    var4 = params[67]
        else:
            if inputs[5] >= 2.5:
                if inputs[6] >= 4.5:
                    var4 = params[68]
                else:
                    var4 = params[69]
            else:
                if inputs[4] >= -0.5:
                    var4 = params[70]
                else:
                    var4 = params[71]
    else:
        if inputs[6] >= 10.5:
            if inputs[7] >= 0.5:
                var4 = params[72]
            else:
                var4 = params[73]
        else:
            if inputs[3] >= 5.5550003:
                if inputs[5] >= 1.5:
                    var4 = params[74]
                else:
                    var4 = params[75]
            else:
                if inputs[5] >= 3.5:
                    var4 = params[76]
                else:
                    var4 = params[77]
    if inputs[0] >= -0.4926736:
        if inputs[1] >= 1.8340769:
            if inputs[0] >= 0.008861526:
                if inputs[5] >= 2.5:
                    var5 = params[78]
                else:
                    var5 = params[79]
            else:
                if inputs[1] >= 2.8562293:
                    var5 = params[80]
                else:
                    var5 = params[81]
        else:
            if inputs[1] >= -1.2360642:
                if inputs[3] >= 4.165:
                    var5 = params[82]
                else:
                    var5 = params[83]
            else:
                if inputs[5] >= 1.5:
                    var5 = params[84]
                else:
                    var5 = params[85]
    else:
        if inputs[1] >= 0.81192434:
            if inputs[4] >= 0.5:
                if inputs[0] >= -0.90757996:
                    var5 = params[86]
                else:
                    var5 = params[87]
            else:
                if inputs[3] >= 1.385:
                    var5 = params[88]
                else:
                    var5 = params[89]
        else:
            if inputs[5] >= 2.5:
                if inputs[0] >= -0.8758979:
                    var5 = params[90]
                else:
                    var5 = params[91]
            else:
                if inputs[1] >= -1.2360642:
                    var5 = params[92]
                else:
                    var5 = params[93]
    if inputs[0] >= 0.20041522:
        if inputs[0] >= 2.0295572:
            if inputs[2] >= -0.40843666:
                if inputs[4] >= -0.5:
                    var6 = params[94]
                else:
                    var6 = params[95]
            else:
                if inputs[0] >= 2.772975:
                    var6 = params[96]
                else:
                    var6 = params[97]
        else:
            if inputs[6] >= 3.5:
                if inputs[11] >= 0.5:
                    var6 = params[98]
                else:
                    var6 = params[99]
            else:
                if inputs[0] >= 0.2598629:
                    var6 = params[100]
                else:
                    var6 = params[101]
    else:
        if inputs[6] >= 10.5:
            if inputs[0] >= -1.1355505:
                if inputs[0] >= -0.25447363:
                    var6 = params[102]
                else:
                    var6 = params[103]
            else:
                var6 = params[104]
        else:
            if inputs[2] >= 0.6156785:
                if inputs[3] >= 9.725:
                    var6 = params[105]
                else:
                    var6 = params[106]
            else:
                if inputs[6] >= 4.5:
                    var6 = params[107]
                else:
                    var6 = params[108]
    if inputs[0] >= -0.53101945:
        if inputs[6] >= 10.5:
            if inputs[3] >= -5.5550003:
                if inputs[11] >= 0.5:
                    var7 = params[109]
                else:
                    var7 = params[110]
            else:
                var7 = params[111]
        else:
            if inputs[3] >= 8.335:
                if inputs[3] >= 16.945:
                    var7 = params[112]
                else:
                    var7 = params[113]
            else:
                if inputs[11] >= 0.5:
                    var7 = params[114]
                else:
                    var7 = params[115]
    else:
        if inputs[6] >= 7.5:
            if inputs[0] >= -1.1889775:
                if inputs[3] >= 9.725:
                    var7 = params[116]
                else:
                    var7 = params[117]
            else:
                var7 = params[118]
        else:
            if inputs[0] >= -1.0966785:
                if inputs[10] >= 0.5:
                    var7 = params[119]
                else:
                    var7 = params[120]
            else:
                if inputs[4] >= -0.5:
                    var7 = params[121]
                else:
                    var7 = params[122]
    if inputs[1] >= 0.81192434:
        if inputs[3] >= 1.385:
            if inputs[3] >= 2.775:
                if inputs[0] >= 0.6119897:
                    var8 = params[123]
                else:
                    var8 = params[124]
            else:
                if inputs[0] >= -1.1440263:
                    var8 = params[125]
                else:
                    var8 = params[126]
        else:
            if inputs[1] >= 1.8340769:
                if inputs[0] >= -1.167934:
                    var8 = params[127]
                else:
                    var8 = params[128]
            else:
                if inputs[0] >= -0.52914894:
                    var8 = params[129]
                else:
                    var8 = params[130]
    else:
        if inputs[1] >= -1.2360642:
            if inputs[3] >= 4.165:
                if inputs[0] >= 0.32328546:
                    var8 = params[131]
                else:
                    var8 = params[132]
            else:
                if inputs[10] >= 0.5:
                    var8 = params[133]
                else:
                    var8 = params[134]
        else:
            if inputs[3] >= 5.5550003:
                if inputs[0] >= -1.2164508:
                    var8 = params[135]
                else:
                    var8 = params[136]
            else:
                if inputs[0] >= 0.29347396:
                    var8 = params[137]
                else:
                    var8 = params[138]
    if inputs[6] >= 6.5:
        if inputs[0] >= -1.1738379:
            if inputs[2] >= 0.6156785:
                if inputs[0] >= 0.45930788:
                    var9 = params[139]
                else:
                    var9 = params[140]
            else:
                if inputs[0] >= 2.6381216:
                    var9 = params[141]
                else:
                    var9 = params[142]
        else:
            if inputs[2] >= 0.6156785:
                if inputs[0] >= -1.1889775:
                    var9 = params[143]
                else:
                    var9 = params[144]
            else:
                if inputs[9] >= 0.5:
                    var9 = params[145]
                else:
                    var9 = params[146]
    else:
        if inputs[5] >= 3.5:
            if inputs[0] >= -1.1991484:
                if inputs[0] >= 0.5094614:
                    var9 = params[147]
                else:
                    var9 = params[148]
            else:
                var9 = params[149]
        else:
            if inputs[2] >= -0.40843666:
                if inputs[13] >= 0.5:
                    var9 = params[150]
                else:
                    var9 = params[151]
            else:
                if inputs[1] >= -0.2120699:
                    var9 = params[152]
                else:
                    var9 = params[153]
    if inputs[6] >= 4.5:
        if inputs[0] >= -0.88887465:
            if inputs[2] >= -0.40843666:
                if inputs[6] >= 7.5:
                    var10 = params[154]
                else:
                    var10 = params[155]
            else:
                if inputs[4] >= 0.5:
                    var10 = params[156]
                else:
                    var10 = params[157]
        else:
            if inputs[4] >= 0.5:
                if inputs[3] >= 4.165:
                    var10 = params[158]
                else:
                    var10 = params[159]
            else:
                if inputs[0] >= -1.1740131:
                    var10 = params[160]
                else:
                    var10 = params[161]
    else:
        if inputs[0] >= -1.0966785:
            if inputs[6] >= 2.5:
                if inputs[0] >= -1.0678023:
                    var10 = params[162]
                else:
                    var10 = params[163]
            else:
                if inputs[4] >= 0.5:
                    var10 = params[164]
                else:
                    var10 = params[165]
        else:
            if inputs[2] >= 0.6156785:
                if inputs[0] >= -1.1775205:
                    var10 = params[166]
                else:
                    var10 = params[167]
            else:
                if inputs[0] >= -1.1268408:
                    var10 = params[168]
                else:
                    var10 = params[169]
    if inputs[0] >= 1.1105437:
        if inputs[0] >= 2.9452972:
            var11 = params[170]
        else:
            if inputs[6] >= 3.5:
                if inputs[2] >= -0.40843666:
                    var11 = params[171]
                else:
                    var11 = params[172]
            else:
                if inputs[3] >= 6.9449997:
                    var11 = params[173]
                else:
                    var11 = params[174]
    else:
        if inputs[1] >= 0.81192434:
            if inputs[5] >= 2.5:
                if inputs[0] >= -0.13610435:
                    var11 = params[175]
                else:
                    var11 = params[176]
            else:
                if inputs[0] >= -0.102727115:
                    var11 = params[177]
                else:
                    var11 = params[178]
        else:
            if inputs[2] >= 0.6156785:
                if inputs[6] >= 9.5:
                    var11 = params[179]
                else:
                    var11 = params[180]
            else:
                if inputs[6] >= 3.5:
                    var11 = params[181]
                else:
                    var11 = params[182]
    if inputs[6] >= 11.5:
        if inputs[0] >= -1.0830588:
            if inputs[0] >= -0.7648938:
                if inputs[0] >= -0.7618542:
                    var12 = params[183]
                else:
                    var12 = params[184]
            else:
                var12 = params[185]
        else:
            var12 = params[186]
    else:
        if inputs[2] >= 1.6397938:
            if inputs[0] >= -1.0583327:
                if inputs[0] >= -0.88460755:
                    var12 = params[187]
                else:
                    var12 = params[188]
            else:
                if inputs[0] >= -1.1504562:
                    var12 = params[189]
                else:
                    var12 = params[190]
        else:
            if inputs[0] >= 0.30399567:
                if inputs[2] >= 0.6156785:
                    var12 = params[191]
                else:
                    var12 = params[192]
            else:
                if inputs[4] >= -1.5:
                    var12 = params[193]
                else:
                    var12 = params[194]
    if inputs[0] >= -0.6066004:
        if inputs[0] >= -0.6060159:
            if inputs[1] >= 1.8340769:
                if inputs[2] >= -0.40843666:
                    var13 = params[195]
                else:
                    var13 = params[196]
            else:
                if inputs[5] >= 1.5:
                    var13 = params[197]
                else:
                    var13 = params[198]
        else:
            var13 = params[199]
    else:
        if inputs[0] >= -1.241469:
            if inputs[1] >= -0.72406703:
                if inputs[4] >= 0.5:
                    var13 = params[200]
                else:
                    var13 = params[201]
            else:
                if inputs[13] >= 0.5:
                    var13 = params[202]
                else:
                    var13 = params[203]
        else:
            if inputs[4] >= 0.5:
                if inputs[0] >= -1.2780613:
                    var13 = params[204]
                else:
                    var13 = params[205]
            else:
                var13 = params[206]
    if inputs[4] >= 1.5:
        if inputs[1] >= -0.72406703:
            if inputs[6] >= 3.5:
                if inputs[11] >= 0.5:
                    var14 = params[207]
                else:
                    var14 = params[208]
            else:
                if inputs[7] >= 0.5:
                    var14 = params[209]
                else:
                    var14 = params[210]
        else:
            if inputs[4] >= 2.5:
                var14 = params[211]
            else:
                var14 = params[212]
    else:
        if inputs[6] >= 2.5:
            if inputs[9] >= 0.5:
                if inputs[4] >= 0.5:
                    var14 = params[213]
                else:
                    var14 = params[214]
            else:
                if inputs[1] >= -0.72406703:
                    var14 = params[215]
                else:
                    var14 = params[216]
        else:
            if inputs[4] >= 0.5:
                if inputs[8] >= 0.5:
                    var14 = params[217]
                else:
                    var14 = params[218]
            else:
                if inputs[3] >= -1.39:
                    var14 = params[219]
                else:
                    var14 = params[220]
    if inputs[6] >= 4.5:
        if inputs[2] >= -0.40843666:
            if inputs[3] >= 1.385:
                if inputs[13] >= 0.5:
                    var15 = params[221]
                else:
                    var15 = params[222]
            else:
                if inputs[5] >= 2.5:
                    var15 = params[223]
                else:
                    var15 = params[224]
        else:
            if inputs[4] >= 0.5:
                if inputs[5] >= 1.5:
                    var15 = params[225]
                else:
                    var15 = params[226]
            else:
                if inputs[3] >= 8.335:
                    var15 = params[227]
                else:
                    var15 = params[228]
    else:
        if inputs[4] >= 1.5:
            if inputs[0] >= -1.2207179:
                if inputs[13] >= 0.5:
                    var15 = params[229]
                else:
                    var15 = params[230]
            else:
                var15 = params[231]
        else:
            if inputs[2] >= -0.40843666:
                if inputs[5] >= 3.5:
                    var15 = params[232]
                else:
                    var15 = params[233]
            else:
                if inputs[3] >= 16.94:
                    var15 = params[234]
                else:
                    var15 = params[235]
    if inputs[1] >= -1.2360642:
        if inputs[3] >= 1.385:
            if inputs[0] >= -0.28451902:
                if inputs[3] >= 2.775:
                    var16 = params[236]
                else:
                    var16 = params[237]
            else:
                if inputs[8] >= 0.5:
                    var16 = params[238]
                else:
                    var16 = params[239]
        else:
            if inputs[0] >= 2.6961663:
                if inputs[8] >= 0.5:
                    var16 = params[240]
                else:
                    var16 = params[241]
            else:
                if inputs[2] >= -0.40843666:
                    var16 = params[242]
                else:
                    var16 = params[243]
    else:
        if inputs[0] >= -1.0745245:
            if inputs[0] >= -1.0508506:
                if inputs[3] >= 9.725:
                    var16 = params[244]
                else:
                    var16 = params[245]
            else:
                if inputs[9] >= 0.5:
                    var16 = params[246]
                else:
                    var16 = params[247]
        else:
            if inputs[8] >= 0.5:
                if inputs[4] >= 0.5:
                    var16 = params[248]
                else:
                    var16 = params[249]
            else:
                if inputs[4] >= 1.5:
                    var16 = params[250]
                else:
                    var16 = params[251]
    if inputs[1] >= 1.8340769:
        if inputs[0] >= 3.0555997:
            var17 = params[252]
        else:
            if inputs[2] >= -0.40843666:
                if inputs[4] >= -1.5:
                    var17 = params[253]
                else:
                    var17 = params[254]
            else:
                if inputs[6] >= 3.5:
                    var17 = params[255]
                else:
                    var17 = params[256]
    else:
        if inputs[0] >= -1.2234068:
            if inputs[0] >= -1.1792741:
                if inputs[0] >= -1.1776373:
                    var17 = params[257]
                else:
                    var17 = params[258]
            else:
                if inputs[6] >= 6.5:
                    var17 = params[259]
                else:
                    var17 = params[260]
        else:
            if inputs[5] >= 2.5:
                if inputs[0] >= -1.2355652:
                    var17 = params[261]
                else:
                    var17 = params[262]
            else:
                if inputs[0] >= -1.2304213:
                    var17 = params[263]
                else:
                    var17 = params[264]
    if inputs[2] >= 1.6397938:
        if inputs[8] >= 0.5:
            if inputs[5] >= 2.5:
                if inputs[0] >= 0.25588804:
                    var18 = params[265]
                else:
                    var18 = params[266]
            else:
                if inputs[0] >= -0.043630145:
                    var18 = params[267]
                else:
                    var18 = params[268]
        else:
            if inputs[6] >= 10.5:
                if inputs[0] >= 0.039666772:
                    var18 = params[269]
                else:
                    var18 = params[270]
            else:
                if inputs[0] >= -1.0241957:
                    var18 = params[271]
                else:
                    var18 = params[272]
    else:
        if inputs[6] >= 9.5:
            if inputs[5] >= 2.5:
                if inputs[0] >= -1.0833511:
                    var18 = params[273]
                else:
                    var18 = params[274]
            else:
                if inputs[1] >= -0.72406703:
                    var18 = params[275]
                else:
                    var18 = params[276]
        else:
            if inputs[2] >= 0.6156785:
                if inputs[5] >= 2.5:
                    var18 = params[277]
                else:
                    var18 = params[278]
            else:
                if inputs[6] >= 5.5:
                    var18 = params[279]
                else:
                    var18 = params[280]
    if inputs[0] >= 1.562393:
        if inputs[0] >= 3.5200167:
            var19 = params[281]
        else:
            if inputs[2] >= 1.6397938:
                var19 = params[282]
            else:
                if inputs[6] >= 9.5:
                    var19 = params[283]
                else:
                    var19 = params[284]
    else:
        if inputs[0] >= 1.4279487:
            if inputs[7] >= 0.5:
                if inputs[4] >= 0.5:
                    var19 = params[285]
                else:
                    var19 = params[286]
            else:
                var19 = params[287]
        else:
            if inputs[0] >= -1.2381372:
                if inputs[0] >= -1.1435586:
                    var19 = params[288]
                else:
                    var19 = params[289]
            else:
                if inputs[2] >= 0.6156785:
                    var19 = params[290]
                else:
                    var19 = params[291]
    if inputs[3] >= -2.775:
        if inputs[6] >= 2.5:
            if inputs[11] >= 0.5:
                if inputs[3] >= 4.165:
                    var20 = params[292]
                else:
                    var20 = params[293]
            else:
                if inputs[1] >= -0.2120699:
                    var20 = params[294]
                else:
                    var20 = params[295]
        else:
            if inputs[4] >= -0.5:
                if inputs[4] >= 0.5:
                    var20 = params[296]
                else:
                    var20 = params[297]
            else:
                if inputs[1] >= 0.81192434:
                    var20 = params[298]
                else:
                    var20 = params[299]
    else:
        if inputs[7] >= 0.5:
            var20 = params[300]
        else:
            if inputs[6] >= 11.5:
                var20 = params[301]
            else:
                if inputs[6] >= 7.5:
                    var20 = params[302]
                else:
                    var20 = params[303]
    if inputs[0] >= -0.18257526:
        if inputs[4] >= -1.5:
            if inputs[0] >= -0.07835181:
                if inputs[2] >= 1.6397938:
                    var21 = params[304]
                else:
                    var21 = params[305]
            else:
                if inputs[5] >= 1.5:
                    var21 = params[306]
                else:
                    var21 = params[307]
        else:
            if inputs[6] >= 5.5:
                if inputs[11] >= 0.5:
                    var21 = params[308]
                else:
                    var21 = params[309]
            else:
                var21 = params[310]
    else:
        if inputs[0] >= -0.19888392:
            var21 = params[311]
        else:
            if inputs[0] >= -0.53101945:
                if inputs[13] >= 0.5:
                    var21 = params[312]
                else:
                    var21 = params[313]
            else:
                if inputs[4] >= 0.5:
                    var21 = params[314]
                else:
                    var21 = params[315]
    if inputs[5] >= 3.5:
        if inputs[0] >= -0.8305961:
            if inputs[6] >= 4.5:
                var22 = params[316]
            else:
                if inputs[8] >= 0.5:
                    var22 = params[317]
                else:
                    var22 = params[318]
        else:
            if inputs[6] >= 10.5:
                var22 = params[319]
            else:
                var22 = params[320]
    else:
        if inputs[5] >= 1.5:
            if inputs[2] >= -0.40843666:
                if inputs[3] >= -5.5550003:
                    var22 = params[321]
                else:
                    var22 = params[322]
            else:
                if inputs[5] >= 2.5:
                    var22 = params[323]
                else:
                    var22 = params[324]
        else:
            if inputs[3] >= -5.5550003:
                if inputs[2] >= 2.663909:
                    var22 = params[325]
                else:
                    var22 = params[326]
            else:
                if inputs[8] >= 0.5:
                    var22 = params[327]
                else:
                    var22 = params[328]
    if inputs[6] >= 3.5:
        if inputs[3] >= 16.665:
            var23 = params[329]
        else:
            if inputs[0] >= -0.8443327:
                if inputs[3] >= -5.5550003:
                    var23 = params[330]
                else:
                    var23 = params[331]
            else:
                if inputs[3] >= -4.17:
                    var23 = params[332]
                else:
                    var23 = params[333]
    else:
        if inputs[7] >= 0.5:
            if inputs[0] >= -1.0372308:
                var23 = params[334]
            else:
                if inputs[1] >= 0.81192434:
                    var23 = params[335]
                else:
                    var23 = params[336]
        else:
            if inputs[0] >= 0.5085846:
                if inputs[1] >= -0.2120699:
                    var23 = params[337]
                else:
                    var23 = params[338]
            else:
                var23 = params[339]
    if inputs[6] >= 7.5:
        if inputs[2] >= 1.6397938:
            if inputs[0] >= -1.1504562:
                if inputs[0] >= -0.96270204:
                    var24 = params[340]
                else:
                    var24 = params[341]
            else:
                var24 = params[342]
        else:
            if inputs[4] >= 1.5:
                if inputs[0] >= -0.22103798:
                    var24 = params[343]
                else:
                    var24 = params[344]
            else:
                if inputs[3] >= -5.5550003:
                    var24 = params[345]
                else:
                    var24 = params[346]
    else:
        if inputs[2] >= -0.40843666:
            if inputs[5] >= 1.5:
                if inputs[3] >= 9.725:
                    var24 = params[347]
                else:
                    var24 = params[348]
            else:
                if inputs[7] >= 0.5:
                    var24 = params[349]
                else:
                    var24 = params[350]
        else:
            if inputs[0] >= -1.0936389:
                if inputs[3] >= 9.725:
                    var24 = params[351]
                else:
                    var24 = params[352]
            else:
                if inputs[0] >= -1.095568:
                    var24 = params[353]
                else:
                    var24 = params[354]
    if inputs[4] >= 2.5:
        var25 = params[355]
    else:
        if inputs[5] >= 1.5:
            if inputs[2] >= 0.6156785:
                if inputs[5] >= 2.5:
                    var25 = params[356]
                else:
                    var25 = params[357]
            else:
                if inputs[4] >= -0.5:
                    var25 = params[358]
                else:
                    var25 = params[359]
        else:
            if inputs[2] >= 1.6397938:
                if inputs[4] >= -0.5:
                    var25 = params[360]
                else:
                    var25 = params[361]
            else:
                if inputs[3] >= 2.775:
                    var25 = params[362]
                else:
                    var25 = params[363]
    if inputs[0] >= -0.12295219:
        if inputs[0] >= -0.09384212:
            if inputs[0] >= -0.09273149:
                if inputs[6] >= 4.5:
                    var26 = params[364]
                else:
                    var26 = params[365]
            else:
                var26 = params[366]
        else:
            if inputs[3] >= 2.775:
                if inputs[6] >= 3.5:
                    var26 = params[367]
                else:
                    var26 = params[368]
            else:
                if inputs[0] >= -0.10927397:
                    var26 = params[369]
                else:
                    var26 = params[370]
    else:
        if inputs[0] >= -0.15434198:
            if inputs[0] >= -0.14627534:
                if inputs[0] >= -0.14352798:
                    var26 = params[371]
                else:
                    var26 = params[372]
            else:
                var26 = params[373]
        else:
            if inputs[0] >= -0.15632942:
                if inputs[5] >= 2.5:
                    var26 = params[374]
                else:
                    var26 = params[375]
            else:
                if inputs[0] >= -0.53101945:
                    var26 = params[376]
                else:
                    var26 = params[377]
    if inputs[1] >= 0.81192434:
        if inputs[7] >= 0.5:
            if inputs[4] >= -1.5:
                if inputs[2] >= 0.6156785:
                    var27 = params[378]
                else:
                    var27 = params[379]
            else:
                var27 = params[380]
        else:
            var27 = params[381]
    else:
        if inputs[11] >= 0.5:
            if inputs[4] >= 1.5:
                var27 = params[382]
            else:
                if inputs[2] >= -0.40843666:
                    var27 = params[383]
                else:
                    var27 = params[384]
        else:
            if inputs[1] >= -0.2120699:
                if inputs[3] >= 4.165:
                    var27 = params[385]
                else:
                    var27 = params[386]
            else:
                var27 = params[387]
    if inputs[0] >= -1.200376:
        if inputs[6] >= 6.5:
            if inputs[4] >= 0.5:
                if inputs[2] >= 0.6156785:
                    var28 = params[388]
                else:
                    var28 = params[389]
            else:
                if inputs[1] >= 2.8562293:
                    var28 = params[390]
                else:
                    var28 = params[391]
        else:
            if inputs[0] >= -1.1789818:
                if inputs[1] >= 0.81192434:
                    var28 = params[392]
                else:
                    var28 = params[393]
            else:
                if inputs[4] >= 0.5:
                    var28 = params[394]
                else:
                    var28 = params[395]
    else:
        if inputs[2] >= 0.6156785:
            var28 = params[396]
        else:
            if inputs[6] >= 3.5:
                if inputs[10] >= 0.5:
                    var28 = params[397]
                else:
                    var28 = params[398]
            else:
                var28 = params[399]
    if inputs[2] >= -0.40843666:
        if inputs[0] >= -1.0989583:
            if inputs[0] >= -1.0953926:
                if inputs[0] >= -1.0896641:
                    var29 = params[400]
                else:
                    var29 = params[401]
            else:
                var29 = params[402]
        else:
            if inputs[0] >= -1.1170206:
                if inputs[6] >= 9.0:
                    var29 = params[403]
                else:
                    var29 = params[404]
            else:
                if inputs[7] >= 0.5:
                    var29 = params[405]
                else:
                    var29 = params[406]
    else:
        if inputs[0] >= -1.0439532:
            if inputs[0] >= -1.0098159:
                if inputs[0] >= 0.7677696:
                    var29 = params[407]
                else:
                    var29 = params[408]
            else:
                if inputs[6] >= 3.5:
                    var29 = params[409]
                else:
                    var29 = params[410]
        else:
            if inputs[0] >= -1.0448884:
                var29 = params[411]
            else:
                if inputs[6] >= 6.5:
                    var29 = params[412]
                else:
                    var29 = params[413]
    return 0.5 + (var0 + var1 + var2 + var3 + var4 + var5 + var6 + var7 + var8 + var9 + var10 + var11 + var12 + var13 + var14 + var15 + var16 + var17 + var18 + var19 + var20 + var21 + var22 + var23 + var24 + var25 + var26 + var27 + var28 + var29)

def batch_loss(params, inputs, targets):
    error = 0
    for x, y in zip(inputs, targets):
        preds = score(params, x)
        error += (preds - y) ** 2
    return error
