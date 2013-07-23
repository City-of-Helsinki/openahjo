class Policymaker extends Backbone.Tastypie.Model
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

pm_list = new PolicymakerList null,
    filters:
        # Access only the policymakers that have some related
        # material (meetings etc.).
        abbreviation__isnull: false
        limit: 1000

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
    gov = list.filter (m) -> m.get_category() == 'government'
    render_pm_section gov, null, true

    council = list.filter (m) -> m.get_category() == 'council'
    render_pm_section council, null, true

    committees = list.filter (m) -> m.get_category() == 'committee'
    render_pm_section committees, "Lautakunnat", false

    boards = list.filter (m) -> m.get_category() == 'board'
    render_pm_section boards, "Johtokunnat", true

    others = list.filter (m) -> m.get_category() == 'other'
    render_pm_section others, "Muut", true


pm_list.fetch
    success: ->
        render_policymakers pm_list
