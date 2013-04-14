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

$.getJSON API_PREFIX + 'v1/item/', {limit: 1000}, (data) ->
    for item in data.objects
        if not item.geometries.length
            continue
        for geom in item.geometries
            coords = geom.coordinates
            marker = L.marker [coords[1], coords[0]]
            marker.bindPopup "<b>#{geom.name}</b><br>#{item.subject}"
            marker.addTo map
            console.log coords
        console.log item

console.log "here"
