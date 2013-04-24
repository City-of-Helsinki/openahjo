DATE_FORMAT = 'D.M.YYYY'
TRANSLATIONS = {
    "draft resolution": "Päätösesitys"
    "presenter": "Esittelijä"
    "resolution": "Päätös"
    "summary": "Yhteenveto"
}

active_agenda_item = null
active_item = null
agenda_item_list = []

item_template = Handlebars.compile $("#item-template").html()

render_item = (agenda_item) ->
    item_html = item_template agenda_item
    $("#item-details").html item_html
    $(".item-details .meeting-link").click (ev) ->
        id = $(this).data('agenda-item-id')
        item = active_agenda_item.item
        ai_list = agenda_item_list
        for ai in ai_list
            if ai.id == id
                if active_agenda_item == ai
                    break
                render_agenda_item ai
                break
    if agenda_item.item.geometries
        map = L.map($(".item-details .map")[0])
        markers = []
        for geom in agenda_item.item.geometries
            coords = geom.coordinates
            ll = new L.LatLng coords[1], coords[0]
            marker = L.marker ll
            marker.bindPopup "<b>#{geom.name}</b>"
            markers.push marker
        bounds = new L.LatLngBounds (m.getLatLng() for m in markers)
        map.addLayer leaflet_default_layer
        max_zoom = map._layersMaxZoom
        map._layersMaxZoom = 14
        map.fitBounds bounds
        map._layersMaxZoom = max_zoom
        for m in markers
            map.addLayer m

format_agenda_item = (ai) ->
    date = moment ai.meeting.date
    ai.meeting.date_str = date.format(DATE_FORMAT)
    if active_agenda_item == ai
        ai.is_active = true
    else
        ai.is_active = false
    for c in ai.content
        c.type_str = TRANSLATIONS[c.type]

render_agenda_item = (active_ai) ->
    future_list = []
    past_list = []
    now = moment()
    active_agenda_item = active_ai
    for ai in agenda_item_list
        format_agenda_item ai
        date = moment ai.meeting.date
        if date > now
            future_list.push ai
        else
            past_list.push ai
    item = active_item
    item.future_list = future_list
    item.past_list = past_list
    active_ai.item = item
    render_item active_agenda_item

item_id = window.active_item_id
$.getJSON "#{API_PREFIX}v1/item/#{window.active_item_id}/", (item) ->
    active_item = item
    $.getJSON "#{API_PREFIX}v1/agenda_item/", {item: item_id, order_by: '-meeting__date'}, (data) ->
        agenda_item_list = data.objects
        render_agenda_item agenda_item_list[0]
