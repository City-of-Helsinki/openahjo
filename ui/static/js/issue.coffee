render_item = (agenda_item) ->
    agenda_item.meeting_template = meeting_template
    item_html = item_template agenda_item
    $(".item-details").html item_html

    $(".meeting-list li").click (ev) ->
        id = $(this).data('agenda-item-id')
        item = active_agenda_item.item
        ai_list = agenda_item_list
        for ai in ai_list
            if ai.id == id
                if active_agenda_item == ai
                    break
                render_agenda_item ai
                break
    map_container = $(".item-details .map")
    if agenda_item.issue.geometries.length
        map = L.map map_container[0]
        map.addLayer leaflet_default_layer
        if map_markers
            for m in map_markers
                map.removeLayer m
        map_geometries = []
        for geojson_geom in agenda_item.issue.geometries
            geom = L.geoJson geojson_geom
            geom.bindPopup "<b>#{geojson_geom.name}</b>"
            map_geometries.push geom
        layer_group = L.featureGroup map_geometries
        bounds = layer_group.getBounds()
        layer_group.addTo map
        if false
            max_zoom = map._layersMaxZoom
            map._layersMaxZoom = 14
            map.fitBounds bounds
            map._layersMaxZoom = max_zoom
        else
            map.setView bounds.getCenter(), 14, true
        L.Util.requestAnimFrame map.invalidateSize, map
        window.map = map

format_agenda_item = (ai) ->
    date = moment ai.meeting.date
    ai.meeting.date_str = date.format(DATE_FORMAT)
    if active_agenda_item == ai
        ai.is_active = true
    else
        ai.is_active = false
    if ai.resolution
        ai.resolution_str = RESOLUTIONS_FI[ai.resolution]
        ai.resolution_icon = RESOLUTIONS_ICONS[ai.resolution]
    ai.has_non_public_attachments = false
    for c in ai.content
        c.type_str = TRANSLATIONS[c.type]

video_player = null
video_url = null

play_video = (ev) ->
    ev.preventDefault()
    vid_id = parseInt $(this).data('id')
    video = null
    for v in active_agenda_item.video_list
        if v.id == vid_id
            video = v
            break
    # Setup modal dialog
    $modal = $("#video-playback-modal")
    $modal.find(".modal-header h3").html(active_agenda_item.subject)

    show_modal = ->
        $modal.on 'hide', ->
            player = _V_("video")
            player.pause()
            $modal.off 'hide'
        $modal.modal()

    if video_player?
        if video.url == video_url
            $modal.on 'shown', ->
                video_player.currentTime video.start_pos
                video_player.play()
            show_modal()
            return
        else
            video_player.dispose()
            video_player = null
            $modal.find("video").remove()

    $vid_el = $("""
    <video id="video" class="video-js vjs-default-skin" controls preload="auto" width="512" height="288">
        <p>Video Playback Not Supported</p>
    </video>""")
    if video.local_copies?
        # If there are local copies of the videos, prefer those.
        for mime_type of video.local_copies
            $vid_el.append $("<source src='#{video.local_copies[mime_type]}' type='#{mime_type}'>")
    else
        $vid_el.append $("<source src='#{video.url}' type='video/mp4'>")

    $modal.find(".modal-body").append $vid_el
    # Initialize video player
    player = videojs "video",
        preload: "metadata"
        poster: video.screenshot_uri
        autoplay: true
    player.on "loadedmetadata", ->
        player.currentTime video.start_pos
        player.off "loadedmetadata"
    video_url = video.url
    video_player = player
    show_modal()

render_videos = (video_list) ->
    $ul = $("#video-list")
    for vid in video_list
        if vid.speaker
            title = vid.speaker
            if vid.party
                title += "<br />" + vid.party
        else if vid.index == 0
            title = "Asian käsittely"
        $el = $("<li data-id='#{vid.id}'><a href='#'>#{title}</a></li>")
        $ul.append $el
        $el.click play_video
    if video_list.length
        $ul.show()

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
    issue = active_issue
    issue.future_list = future_list
    issue.past_list = past_list
    active_ai.issue = issue
    render_item active_agenda_item
    if active_agenda_item.video_list?
        render_videos active_agenda_item.video_list
    else
        $.getJSON "#{API_PREFIX}v1/video/", {agenda_item: active_agenda_item.id, limit: 500}, (data) ->
            active_agenda_item.video_list = data.objects
            render_videos active_agenda_item.video_list

issue_id = window.active_issue_id
$.getJSON "#{API_PREFIX}v1/issue/#{issue_id}/", (issue) ->
    active_issue = issue
    $.getJSON "#{API_PREFIX}v1/agenda_item/", {issue: issue_id, order_by: '-meeting__date'}, (data) ->
        agenda_item_list = data.objects
        render_agenda_item agenda_item_list[0]
