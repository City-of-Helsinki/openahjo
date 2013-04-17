GEOCODER_BASE = "http://dev.hel.fi/geocoder/v1/"

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

###$.getJSON '/v1/meeting/', (data) ->
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
    #key: '8831a03368004097ba8ddc389ec30633'
    key: 'BC9A493B41014CAABB98F0471D759707'
    style: 998
).addTo(map);
window.my_map = map

active_borders = null

markers = []
refresh_items = (bounds) ->
    params = {limit: 1000}
    if bounds
        params['bbox'] = bounds.toBBoxString()
    for m in markers
        map.removeLayer m
    $.getJSON API_PREFIX + 'v1/item/', params, (data) ->
        for item in data.objects
            if not item.geometries.length
                continue
            for geom in item.geometries
                coords = geom.coordinates
                ll = new L.LatLng coords[1], coords[0]
                if active_borders
                    if not leafletPip.pointInLayer(ll, active_borders).length
                        continue
                marker = L.marker ll
                marker.bindPopup "<b>#{geom.name}</b><br><a href='#'>#{item.subject}</a>"
                marker.addTo map
                markers.push marker

input_district_map = null
$("#district-input").typeahead(
    source: (query, process_cb) ->
        $.getJSON(GEOCODER_BASE + 'district/', {input: query}, (data) ->
            objs = data.objects
            ret = []
            input_addr_map = []
            for obj in objs
                ret.push(obj.name)
            input_district_map = objs
            process_cb(ret)
        )
)

$("#district-input").on 'change', ->
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

refresh_items()
