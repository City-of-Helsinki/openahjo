committees = {}
selected_committee = null

$.getJSON API_PREFIX + 'v1/committee/', {order_by: 'name', meetings: true}, (data) ->
    $list = $('#committee-list')
    $list.append $('<li class="nav-header">Päättäjät</li>')
    for obj in data.objects
        $el = $("<li><a href='#' data-id='#{obj.id}'>#{obj.name}</a></li>")
        $list.append $el
        committees[obj.id] = obj
    $list.find('a').click (ev) ->
        id = $(this).data 'id'
        selected_committee = committees[id]
        $list.find('li').removeClass 'active'
        $(this).parent().addClass 'active'
        refresh_meetings()

show_meeting = (meeting, $parent) ->
    $next = $parent.next()
    if $next.prop('tagName') == 'OL'
        if $next.is(':visible')
            $next.slideUp()
        else
            $next.slideDown()
        return

    $.getJSON API_PREFIX + 'v1/agenda_item/', {meeting: meeting.id, order_by: 'index'}, (data) ->
        $list = $("<ol></ol>")
        for obj in data.objects
            url = "#{API_PREFIX}issue/#{obj.issue.slug}/"
            if obj.issue.summary
                summary = obj.issue.summary
            else
                summary = ''
            $el = $("<li value='#{obj.index}'><h4><a href='#{url}'>#{obj.issue.subject}</h4></a><div class='content'>#{summary}</div></li>")
            $list.append $el
        $list.hide()
        $parent.after $list
        $list.slideDown()

refresh_meetings = ->
    params = {}
    if selected_committee
        params['committee'] = selected_committee.id
    $.getJSON API_PREFIX + 'v1/meeting/', params, (data) ->
        $list = $('#meeting-list')
        $list.empty()
        for obj in data.objects
          do (obj) ->
            date = obj.date.split('-')
            date_str = "#{date[2]}.#{date[1]}.#{date[0]}"
            $el = $('<button class="btn btn-large btn-block">' + obj.committee_name + ' ' + obj.number + '/' + obj.year + " (#{date_str})</a>")
            $list.append $el
            $el.click (ev) ->
                show_meeting obj, $el
