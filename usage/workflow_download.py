from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
584657
610081
588109
609436
609880
592048
601124
581515
614644
502333
609442
592749
539890
527307
526668
542216
526420
609443
563510
554246
598422
549896
588804
527518
587806
552179
614186
569869
622705
609438
609439
581514
604612
1230612
1214450
1244791
1224926
1191725
1177497
1297601
1205848
1177499
364357
364356
398928
610650
1175299
1126347
1233445
609433
610077
610045
617299
560461
586478
1202421
544397
457404
605923
1221166
417470
1208725
616494
616493
616495
1074200
472255
1248780
1183392
1312143
1224842
360100
613956
1208447
1237235
1205089
641737
1229293
1198557
1110640
1180204
1210472
1212291
1230564
1237061
1236185
1237060
1236179
1218673
1209074
1246231
1220295
1212685
1224729
1149095
1055267
1210653
1082835
1175301
1195945
1169211
1132004
548399
335274
465606
391364
335275
308882
391365
335276
479462
465714
321732
374042
459050
304599
541307
495064
485051
459074
308349
304596
441039
507307
402766
559463
429985
530545
355998
340774
1198628
384189
499442
576736
412010
1212510
394904
1088843
366527
622384
423375
304598
518077
1031043
1224694
646436
1128084
304611
1179818
1060432
1236577
381188
398381
1232926
1213741
1254674
1251332
1251328
1251330
1256654
1256655
1251274
1254676
1251331
1251337
1251336
1251333
1251327
1251335
1251276
1251312
1251320
1251334
1251329
1251317
1257793
1251313
1275917
1275909
1276001
1275875
1220323
1231866
405527
427438
465305
324098
420264
447881
450250
404378
386201
418191
324100
1178245
324099
473770
1100526
1091453
1093929
1190386
618051
618043
1199600
618050
618049
597978
1147162
1073181
1199023
629026
1236057
1072755
614157
609281
611623
584001
599889
613989
616497
573968
1192396
1024194
1020557
1122276
622378
594215
638868
644940
1202419
1021324
1015038
617171
622371
622373
1250988
594220
1146452
1048131
594221
594217
1079883
1043077
1250580
594218
1114792
622374
1175645
594219
1063183
1057824
1233270
1233295
1233301
1233299
1233272
1233300
1233297
1233313
1233317
1233298
1233296
1233269
1233314
1233319
1233318
1233315
1187390
629911
616238
614590
605917
1199125
1199123
1134570
278727
278719
476051
416157
401313
388982
481138
396788
416158
368071
481139
1218566
1167280
1167278
1123927
1163646
1189957
548217
536899
500081
528927
1045836
577774
1048600




'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)

    pdf_option = env('PDF_OPTION', None)
    if pdf_option and pdf_option != '否':
        call_when = 'after_album' if pdf_option == '是 | 本子维度合并pdf' else 'after_photo'
        plugin = [{
            'plugin': Img2pdfPlugin.plugin_key,
            'kwargs': {
                'pdf_dir': option.dir_rule.base_dir + '/pdf/',
                'filename_rule': call_when[6].upper() + 'id',
                'delete_original_file': True,
            }
        }]
        option.plugins[call_when] = plugin


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
