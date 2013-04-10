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
        $el = $('<button class="btn btn-block">' + obj.committee_name + ' ' + obj.number + '/' + obj.year + '</button>')
        $list.append $el
        $el.click (ev) ->
            show_meeting obj, $el
