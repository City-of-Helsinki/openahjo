###
TRANSLATIONS = {
    "draft resolution": "Päätösesitys"
    "presenter": "Esittelijä"
    "resolution": "Päätös"
    "summary": "Yhteenveto"
}

show_meeting = (meeting, $parent) ->
    $next = $parent.next()
    if $next.prop('tagName') == 'OL'
        if $next.is(':visible')
            $next.slideUp()
        else
            $next.slideDown()
        return

    $.getJSON '/v1/agenda_item/', {meeting: meeting.id}, (data) ->
        $list = $("<ol></ol>")
        for obj in data.objects
            console.log obj
            content_html = ''
            for c in obj.content
                if c.type of TRANSLATIONS
                    type = TRANSLATIONS[c.type]
                else
                    type = c.type
                content_html += "<strong>#{type}</strong>#{c.text}"
            $el = $("<li><h4>#{obj.item.subject}</h4><div class='content hide'>#{content_html}</div></li>")
            $list.append $el
            $el.find('h4').css('cursor', 'pointer').click (ev) ->
                content = $(ev.target).parent().find('.content')
                if content.is(':visible')
                    content.slideUp()
                else
                    content.slideDown()
        $list.hide()
        $parent.after $list
        $list.slideDown()

$.getJSON '/v1/meeting/', (data) ->
    $list = $('#meeting-list')
    for obj in data.objects
      do (obj) ->
        $el = $('<button class="btn btn-primary btn-block">' + obj.committee_name + ' ' + obj.number + '/' + obj.year + '</button>')
        $list.append $el
        $el.click (ev) ->
            show_meeting obj, $el
###

map = L.map('map').setView [60.170833, 24.9375], 12
L.tileLayer('http://{s}.tile.cloudmade.com/{key}/{style}/256/{z}/{x}/{y}.png',
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>',
    maxZoom: 18
    key: 'BC9A493B41014CAABB98F0471D759707'
    style: 998
).addTo(map);
window.my_map = map

active_borders = null

items = []
item_template = Handlebars.compile $("#item-list-template").html()

markers = []
refresh_items = (bounds) ->
    params = {limit: 1000}
    if bounds
        params['bbox'] = bounds.toBBoxString()
    list_el = $("#item-list")
    $.getJSON API_PREFIX + 'v1/item/', params, (data) ->
        items = []
        list_el.empty()
        for m in markers
            map.removeLayer m
        markers = []
        for item in data.objects
            if not item.geometries.length
                continue
            item.details_uri = "#{API_PREFIX}item/#{item.slug}/"
            for geom in item.geometries
                coords = geom.coordinates
                ll = new L.LatLng coords[1], coords[0]
                if active_borders
                    if not leafletPip.pointInLayer(ll, active_borders).length
                        continue
                item.in_bounds = true
                marker = L.marker ll
                marker.bindPopup "<b>#{geom.name}</b><br><a href='#{item.details_uri}'>#{item.subject}</a>"
                marker.addTo map
                markers.push marker
            if not item.in_bounds
                continue
            item_html = item_template item
            items.push item
            list_el.append $($.trim(item_html))

input_district_map = null
$(".district-input input").typeahead(
    source: (query, process_cb) ->
        $.getJSON(GEOCODER_API_URL + 'v1/district/', {input: query}, (data) ->
            objs = data.objects
            ret = []
            input_addr_map = []
            for obj in objs
                ret.push(obj.name)
            input_district_map = objs
            process_cb(ret)
        )
)

$(".district-input input").on 'change', ->
    match_obj = null
    for obj in input_district_map
        if obj.name == $(this).val()
            match_obj = obj
            break
    if not match_obj
        return
    if active_borders
        map.removeLayer active_borders
    borders = L.geoJson match_obj.borders,
        style:
            weight: 2
    borders.bindPopup match_obj.name
    borders.addTo map
    active_borders = borders
    map.fitBounds borders.getBounds()
    refresh_items active_borders.getBounds()
    close_btn = $(".district-input .close")
    close_btn.parent().show()

$(".district-input .close").on 'click', (ev) ->
    map.removeLayer active_borders
    active_borders = null
    refresh_items map.getBounds()
    $(this).parent().hide()
    $(".district-input input").val ''
    ev.preventDefault()

map.on 'moveend', (ev) ->
    refresh_items map.getBounds()

refresh_items map.getBounds()
