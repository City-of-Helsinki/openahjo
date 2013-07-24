class Policymaker extends Backbone.Tastypie.Model
    get_view_url: ->
        return API_PREFIX + 'policymaker/' + @get('slug') + '/'
    get_category: ->
        abbrev = @get('abbreviation')
        if not abbrev
            return null
        if abbrev == 'Khs'
            return 'government'
        else if abbrev == 'Kvsto'
            return 'council'
        name = @get('name')
        if name.indexOf('lautakunta') >= 0
            return 'committee'
        if name.indexOf('johtokunta') >= 0 or name.indexOf(' jk') >= 0
            return 'board'

        return 'other'

class PolicymakerList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/policymaker/'
    model: Policymaker

PM_VIEW_INFO =
    'Kslk':
        hyphen_names: ['Kaupunki-', 'suunnittelu-', 'lautakunta']
    'Sotelk':
        hyphen_names: ['Sosiaali-', 'ja terveys-', 'lautakunta']
    'Tplk':
        hyphen_names: ['Teknisen', 'palvelun', 'lautakunta']
    'Vakalk':
        hyphen_names: ['Varhais-', 'kasvatus-', 'lautakunta']
    'Kklk':
        hyphen_names: ['Kulttuuri- ja', 'kirjasto-', 'lautakunta']

class PolicymakerListNavView extends Backbone.View
    el: '.policymaker-nav'

    initialize: ->
        @collection.on 'reset', @render, @
    render: ->
        COMPONENTS = [
            {name: 'Kaupunginvaltuusto', category: 'council'}
            {name: 'Kaupunginhallitus', category: 'government'}
            {name: 'Lautakunnat', category: 'committee'}
            {name: 'Johtokunnat', category: 'board'}
            {name: 'Muut', category: 'other'}
        ]
        @$el.empty()
        @$el.append $("<li class='active'><a href='#'>Päättäjät</a></li>")
        for c in COMPONENTS
            list = @collection.filter (m) -> m.get_category() == c.category
            if list.length > 1
                $li = $("<li class='dropdown'><a class='dropdown-toggle' data-toggle='dropdown' href='#'>#{c.name} <b class='caret'></b>")
                $ul = $("<ul class='dropdown-menu'></ul>")
                $li.append $ul
                list.forEach (m) ->
                    $el = $("<li><a href='#{m.get_view_url()}'>#{m.get 'name'}</a></li>")
                    $ul.append $el
            else
                m = list[0]
                $li = $("<li><a href='#{m.get_view_url()}'>#{c.name}</a></li>")

            $li.addClass c.category
            @$el.append $li

class PolicymakerView extends Backbone.View
    tagName: 'div'
    className: 'org-box'
    template: $("#policymaker-list-template").html()

    format_title: ->
        name = @model.get 'name'
        abbrev = @model.get 'abbreviation'
        if abbrev of PM_VIEW_INFO
            vi = PM_VIEW_INFO[abbrev]
            if 'hyphen_names' of vi
                return vi.hyphen_names.join('<br/>')
        lk_idx = name.indexOf 'lautakunta'
        if lk_idx >= 0
            prev_char = name[lk_idx-1]
            if prev_char != ' ' and prev_char != '-'
                hyphen = '-'
            else
                hyphen = ''
            
            name = name[0..lk_idx-1] + hyphen + '<br/>' + name[lk_idx..]
        return name
    render: ->
        model = @model.toJSON()
        model.title = @format_title()
        model.icon = 'search'
        html = _.template @template, model
        @$el.addClass @model.get_category()
        @$el.append html
        return @

render_pm_section = (list, heading, big) ->
    $container = $(".policymaker-list")
    if heading
        $container.append $("<h2>#{heading}</h2>")
    row_idx = 0
    $row = $("<div class='row'></div>")
    list.forEach (m) ->
        view = new PolicymakerView {model: m}
        view.render()
        $el = view.$el
        $row.append view.$el
        row_idx++
        if big
            $el.addClass 'span9'
            $container.append $row
            $row = $("<div class='row'></div>")
            row_idx = 0
        else
            $el.addClass 'span3'
            if row_idx == 3
                $container.append $row
                row_idx = 0
                $row = $("<div class='row'></div>")
    if row_idx
        $container.append $row

render_policymakers = (list) ->
    council = list.filter (m) -> m.get_category() == 'council'
    render_pm_section council, null, true

    gov = list.filter (m) -> m.get_category() == 'government'
    render_pm_section gov, null, true

    committees = list.filter (m) -> m.get_category() == 'committee'
    render_pm_section committees, "Lautakunnat", false

    boards = list.filter (m) -> m.get_category() == 'board'
    render_pm_section boards, "Johtokunnat", true

    others = list.filter (m) -> m.get_category() == 'other'
    render_pm_section others, "Muut", true

policymaker_list = new PolicymakerList policymakers
pm_nav_view = new PolicymakerListNavView {collection: policymaker_list}
pm_nav_view.render()
render_policymakers policymaker_list
