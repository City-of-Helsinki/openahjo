DATE_FORMAT = 'D.M.YYYY'
TRANSLATIONS = {
    "draft resolution": "Päätösesitys"
    "presenter": "Esittelijä"
    "resolution": "Päätös"
    "summary": "Yhteenveto"
}

active_agenda_item = null

render_item = (agenda_item) ->
    console.log "render"
    console.log agenda_item
    item_html = ich.item_template agenda_item
    $("#item-details").html item_html
    $("#item-details .meeting-link").click (ev) ->
        id = $(this).data('agenda-item-id')
        console.log id
        item = active_agenda_item.item
        ai_list = item.past_list.concat item.future_list
        for ai in ai_list
            console.log ai.id
            if ai.id == id
                active_agenda_item = ai
                ai.item = item
                render_item ai

format_agenda_item = (ai) ->
    date = moment ai.meeting.date
    ai.meeting.date_str = date.format(DATE_FORMAT)
    if active_agenda_item == ai
        ai.is_active = true
    else
        ai.is_active = false
    for c in ai.content
        c.type_str = TRANSLATIONS[c.type]

item_id = window.active_item_id
$.getJSON "#{API_PREFIX}v1/item/#{window.active_item_id}/", (item) ->
    future_list = []
    past_list = []
    now = moment()
    $.getJSON "#{API_PREFIX}v1/agenda_item/", {item: item_id, order_by: '-meeting__date'}, (data) ->
        active_agenda_item = data.objects[0]
        for obj in data.objects
            format_agenda_item obj
            date = moment obj.meeting.date
            if date > now
                future_list.push obj
            else
                past_list.push obj
        item.future_list = future_list
        item.past_list = past_list
        active_agenda_item.item = item
        render_item active_agenda_item
