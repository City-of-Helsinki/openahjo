
old_ajax = Backbone.ajax

install_spinner = (opts, data) ->
    if data instanceof jQuery
        data = el: opts.spinner
    el = data.el

    start_spinning = ->
        args = _.extend {hwaccel: true}, data
        el.spin args

    timeout = setTimeout start_spinning, 200

    success = opts.success
    opts.success = (resp) ->
        clearTimeout timeout
        el.spin false
        if success
            success resp

    error = opts.error
    opts.error = (resp) ->
        clearTimeout timeout
        el.spin false
        if error
            error resp

Backbone.ajax = ->
    opts = arguments[0]
    if opts and opts.spinner
        install_spinner opts, opts.spinner
    old_ajax.apply Backbone, arguments
