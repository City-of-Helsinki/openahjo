att_list = Attachment.objects.all()

for att in att_list:
    if not att.public:
        continue
    sd = att.hash[0:2]
    arr = str(att.file).split('/')
    arr.insert(1, sd)
    fn = '/'.join(arr)
    att.file = fn
    att.save(update_fields=['file'])
