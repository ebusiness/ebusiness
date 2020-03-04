function GetQueryString()
{
    var result = {};
    if( 1 < window.location.search.length )
    {
        // 最初の1文字 (?記号) を除いた文字列を取得する
        var query = window.location.search.substring( 1 );

        // クエリの区切り記号 (&) で文字列を配列に分割する
        var parameters = query.split( '&' );

        for( var i = 0; i < parameters.length; i++ )
        {
            // パラメータ名とパラメータ値に分割する
            var element = parameters[ i ].split( '=' );

            var paramName = decodeURIComponent( element[ 0 ] );
            var paramValue = decodeURIComponent( element[ 1 ] );

            // パラメータ名をキーとして連想配列に追加する
            result[ paramName ] = paramValue;
        }
    }
    return result;
}

function init_select(name)
{
    params = GetQueryString();
    value = params[name];
    if (value != null && value != undefined)
    {
        document.getElementById(name).value = value;
    }
}

function init_select_name(select_id, name)
{
    params = GetQueryString();
    value = params[name];
    if (value != null && value != undefined)
    {
        $("#" + select_id + " option").filter(function() {
            return $(this).text() == value;
        }).prop('selected', true);
    }
}

function init_select_text(select_id, text)
{
    if (text != null && text != undefined)
    {
        $("#" + select_id + " option").filter(function() {
            return $(this).text() == text;
        }).prop('selected', true);
    }
}

function show_mask() {
    mask = $('#mask')
    mask.css('display', 'block');
    mask.css('width', $(document).width());
    mask.css('height', $(document).height());
}

function show_dialog(id_dialog) {
    show_mask();

    dialog = $('#' + id_dialog);
    dialog.css('display', 'block');
    top_position = ($(window).height() - dialog.height()) / 2;
    left_position = ($(window).width() - dialog.width()) / 2;
    dialog.css('top', top_position + "px");
    dialog.css('left', left_position + "px");
}

function hide_dialog(id_dialog) {
    $('#mask').css('display', 'none');
    dialog = $('.dialog');
    dialog.css('display', 'none');
}

function calc_plus_minus(obj) {
    if (obj.id == "id_price") {
        price = parseFloat($("#id_price").val());
        min_hours = parseFloat($("#id_min_hours").val());
        max_hours = parseFloat($("#id_max_hours").val());
        plus_per_hour = Math.round(price / max_hours);
        minus_per_hour = Math.round(price / min_hours);
        $("#id_plus_per_hour").val(plus_per_hour);
        $("#id_minus_per_hour").val(minus_per_hour);
    } else {
        row_id = $(obj).parent().parent().attr("id");
        price = parseFloat($(obj).val());
        obj_min_hour = $("#id_" + row_id + "-min_hours");
        obj_max_hour = $("#id_" + row_id + "-max_hours");
        obj_plus = $("#id_" + row_id + "-plus_per_hour");
        obj_minus = $("#id_" + row_id + "-minus_per_hour");
        min_hours = parseFloat(obj_min_hour.val());
        max_hours = parseFloat(obj_max_hour.val());

        plus_per_hour = Math.round(price / max_hours);
        minus_per_hour = Math.round(price / min_hours);
        obj_plus.val(plus_per_hour);
        obj_minus.val(minus_per_hour);
    }
}

function calc_minus_from_min_hour(obj) {
    if (obj.id == "id_min_hours") {
        price = parseFloat($("#id_price").val());
        min_hours = parseFloat($("#id_min_hours").val());
        minus_per_hour = Math.round(price / min_hours);
        $("#id_minus_per_hour").val(minus_per_hour);
    } else {
        row_id = $(obj).parent().parent().attr("id");
        obj_price = $("#id_" + row_id + "-price");
        obj_min_hour = $("#id_" + row_id + "-min_hours");
        obj_minus = $("#id_" + row_id + "-minus_per_hour");
        price = parseFloat(obj_price.val());
        min_hours = parseFloat(obj_min_hour.val());

        minus_per_hour = Math.round(price / min_hours);
        obj_minus.val(minus_per_hour);
    }
}

function calc_plus_from_max_hour(obj) {
    if (obj.id == "id_max_hours") {
        price = parseFloat($("#id_price").val());
        max_hours = parseFloat($("#id_max_hours").val());
        plus_per_hour = Math.round(price / max_hours);
        $("#id_plus_per_hour").val(plus_per_hour);
    } else {
        row_id = $(obj).parent().parent().attr("id");
        obj_price = $("#id_" + row_id + "-price");
        obj_max_hour = $("#id_" + row_id + "-max_hours");
        obj_plus = $("#id_" + row_id + "-plus_per_hour");
        price = parseFloat(obj_price.val());
        max_hours = parseFloat(obj_max_hour.val());

        plus_per_hour = Math.round(price / max_hours);
        obj_plus.val(plus_per_hour);
    }
}

function calc_extra_hours(obj) {
    let price = $("#id_price").val();
    let min_hours = $("#id_min_hours").val();
    let max_hours = $("#id_max_hours").val();
    let total_hours = $(obj).val();
    let row_id = $(obj).parent().parent().attr("id");
    let obj_extra_hours = $("#id_" + row_id + "-extra_hours");
    let obj_plus = $("#id_plus_per_hour");
    let obj_minus = $("#id_minus_per_hour");
    let obj_value = $("#id_" + row_id + "-price");                     // 価格
    let request_type = $("div.field-request_type div.readonly").text();
    let obj_carryover = $("#id_" + row_id + "-carryover_hours");
    if (min_hours != "" && max_hours != "" && total_hours != "") {
        min_hours = parseFloat(min_hours);
        max_hours = parseFloat(max_hours);
        total_hours = parseFloat(total_hours);
        let extra_hours = 0.00;
        if (request_type === '時給（繰越）') {
            extra_hours = 0;
            obj_carryover.val(total_hours - min_hours);
        } else if (total_hours > max_hours) {
            extra_hours = total_hours - max_hours;
        } else if (total_hours < min_hours) {
            extra_hours = total_hours - min_hours;
        }
        obj_extra_hours.val(extra_hours);

        // 増（円）と 減（円）
        price = parseFloat(price);
        plus_per_hour = Math.round(obj_plus.val());
        minus_per_hour = Math.round(obj_minus.val());
//        obj_plus.val(plus_per_hour);
//        obj_minus.val(minus_per_hour);

        // 最終価格
        if (request_type === '時給（繰越）') {
            // 前月繰越金額取得
            let prev_tr = $("#" + row_id).prev();
            let prev_carryover_hours = 0;
            if (prev_tr && prev_tr.length > 0) {
                prev_carryover_hours = $("#id_" + prev_tr.attr('id') + '-carryover_hours').val();
                prev_carryover_hours = parseFloat(prev_carryover_hours);
            }
            result = price * (prev_carryover_hours + min_hours);
        } else if (extra_hours > 0) {
            result = price + extra_hours * plus_per_hour;
        } else if (extra_hours < 0) {
            result = price + extra_hours * minus_per_hour;
        } else {
            result = price;
        }
        obj_value.val(Math.round(result));
    }
}

function calc_price_for_plus(obj) {
    price = parseFloat($("#id_price").val());
    plus_per_hour = parseFloat($(obj).val());
    row_id = $(obj).parent().parent().attr("id");
    obj_extra_hours = $("#id_" + row_id + "-extra_hours");
    obj_value = $("#id_" + row_id + "-price");                     // 価格
    extra_hours = $(obj_extra_hours).val();
    if (extra_hours != "") {
        extra_hours = parseFloat(extra_hours);
        if (extra_hours > 0) {
            result = price + extra_hours * plus_per_hour;
            obj_value.val(Math.round(result));
        }
    }
}

function calc_price_for_minus(obj) {
    price = parseFloat($("#id_price").val());
    minus_per_hour = parseFloat($(obj).val());
    row_id = $(obj).parent().parent().attr("id");
    obj_extra_hours = $("#id_" + row_id + "-extra_hours");
    obj_value = $("#id_" + row_id + "-price");                     // 価格
    extra_hours = $(obj_extra_hours).val();
    if (extra_hours != "") {
        extra_hours = parseFloat(extra_hours);
        if (extra_hours < 0) {
            result = price + extra_hours * minus_per_hour;
            obj_value.val(Math.round(result));
        }
    }
}

function calc_hourly_pay(obj) {
    let row_id = $(obj).parent().parent().attr("id");
    let total_hours = $(obj).val();
    let hourly_pay = $("#" + row_id + "-hourly_pay").val();
    let obj_value = $("#" + row_id + "-price");                     // 価格
    let basic_hours = $(obj).parent().parent().find('input.carryover-hours').val();
    let prev_carryover = $(obj).parent().parent().find('input.prev-carryover-hours').val();
    let obj_carryover = $("#" + row_id + "-carryover_hours");
    if (basic_hours) {
        basic_hours = parseFloat(basic_hours);
    }
    if (hourly_pay != "" && total_hours != "") {
        if (basic_hours) {
            let total_price = (basic_hours + parseFloat(prev_carryover)) * hourly_pay;
            obj_value.val(Math.round(total_price));
            obj_carryover.val(parseFloat(total_hours) - basic_hours);
        } else {
            let total_price = total_hours * hourly_pay;
            obj_value.val(Math.round(total_price));
        }
    }
}

function get_extra_hours(total_hours, min_hours, max_hours) {
    if (total_hours >= min_hours && total_hours <= max_hours) {
        return 0;
    }
    var attendance_type = $("#hidAttendanceType").val();
    var int_part = Math.floor(total_hours)
    var float_part = (total_hours % 1).toFixed(2)
    if (attendance_type == "1") {
        // １５分ごと
        if (float_part >= 0 && float_part < 0.25) {
            float_part = 0;
        } else if (float_part >= 0.25 && float_part < 0.5) {
            float_part = 0.25;
        } else if (float_part >= 0.5 && float_part < 0.75) {
            float_part = 0.5
        } else {
            float_part = 0.75
        }
    } else if (attendance_type == "2") {
        // ３０分ごと
        if (float_part >= 0 && float_part < 0.5) {
            float_part = 0;
        } else {
            float_part = 0.5
        }
    } else if (attendance_type == "3") {
        // １時間ごと
        float_part = 0;
    } else {
        console.log("識別できない出勤区分です。");
    }

    total_hours = int_part + float_part;
    if (total_hours > max_hours) {
        extra_hours = total_hours - max_hours;
    } else if (total_hours < min_hours) {
        extra_hours = total_hours - min_hours;
    }
    return extra_hours.toFixed(2);
}

function calc_extra_hours_portal(obj) {
    row_id = $(obj).parent().parent().attr("id");
    price = $("#" + row_id + "-basic_price").val();
    min_hours = $("#" + row_id + "-min_hours").val();
    max_hours = $("#" + row_id + "-max_hours").val();
    rate = $("#" + row_id + "-rate").val();
    total_hours = $(obj).val();
    obj_extra_hours = $("#" + row_id + "-extra_hours");
    obj_plus = $("#" + row_id + "-plus_per_hour");
    obj_minus = $("#" + row_id + "-minus_per_hour");
    obj_value = $("#" + row_id + "-price");                     // 価格
    if (min_hours != "" && max_hours != "" && total_hours != "") {
        min_hours = parseFloat(min_hours);
        max_hours = parseFloat(max_hours);
        total_hours = parseFloat(total_hours);
        extra_hours = get_extra_hours(total_hours, min_hours, max_hours);
        rate = parseFloat(rate);
        obj_extra_hours.val(extra_hours);
        // 増（円）と 減（円）
        price = parseFloat(price);
        plus_per_hour = Math.round(obj_plus.val());
        minus_per_hour = Math.round(obj_minus.val());

        // 最終価格
        if (extra_hours > 0) {
            result = price + extra_hours * plus_per_hour;
        }
        else if (extra_hours < 0) {
            result = price + extra_hours * minus_per_hour;
        } else {
            result = price;
        }
        // 小数の処理区分
        var decimal_type = $("#hidDecimalType").val();
        if (decimal_type == 0) {
            // 四捨五入
            obj_value.val(Math.round(result));
        } else {
            // 切り捨て
            obj_value.val(Math.floor(result));
        }
    }
}

function calc_price_for_plus_portal(obj) {
    row_id = $(obj).parent().parent().attr("id");
    price = parseFloat($("#" + row_id + "-basic_price").val());
    plus_per_hour = parseFloat($(obj).val());
    obj_extra_hours = $("#" + row_id + "-extra_hours");
    obj_value = $("#" + row_id + "-price");                     // 価格
    extra_hours = $(obj_extra_hours).val();
    if (extra_hours != "") {
        extra_hours = parseFloat(extra_hours);
        if (extra_hours > 0) {
            result = price + extra_hours * plus_per_hour;
            obj_value.val(Math.round(result));
        }
    }
}

function calc_price_for_minus_portal(obj) {
    row_id = $(obj).parent().parent().attr("id");
    price = parseFloat($("#" + row_id + "-basic_price").val());
    minus_per_hour = parseFloat($(obj).val());
    obj_extra_hours = $("#" + row_id + "-extra_hours");
    obj_value = $("#" + row_id + "-price");                     // 価格
    extra_hours = $(obj_extra_hours).val();
    if (extra_hours != "") {
        extra_hours = parseFloat(extra_hours);
        if (extra_hours < 0) {
            result = price + extra_hours * minus_per_hour;
            obj_value.val(Math.round(result));
        }
    }
}


function row_update_show(obj) {
    row_show = $(obj).parent().parent();
    row_show.css("display", "none");
    
    row_for_update = row_show.next();
    row_for_update.attr("class", "row_updating");
}

function row_update_cancel(obj) {
    row_for_update = $(obj).parent().parent();
    row_for_update.attr("class", "row_updated");

    row_show = row_for_update.prev();
    row_show.css("display", "");
}

function musk() {
    $("body").append("<div class='musk'></div>");
}

function unmask() {
    $("div.musk").remove();
}

function toNum(text) {
    if (text.trim() == "") {
        return 0;
    } else {
        text = text.split(',').join('');
        return parseInt(text);
    }
}

function toNumComma(num) {
    int_comma = (num + "").replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
    return int_comma;
}

function get_business_days(year, month) {
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    var business_days = [];
    $.ajax({
        type: "POST",
        url: "/eb/business_days.html",
        data: {year: year, month: month},
        dataType: "json",
        async: false,
        success: function(ret){
            business_days = ret.business_days;
        }
    });
    return business_days;
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function ajax_get(url, data, callback) {
    return ajax_request(url, "GET", data, callback)
}

function ajax_post(url, data, callback) {
    return ajax_request(url, "POST", data, callback)
}

function ajax_request(url, method, data, callback) {
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    return $.ajax({
        type: method,
        url: url,
        data: data,
        dataType: "json",
        success: callback
    });
}

function setSubOrganizations(obj) {
    if ($(obj).val() == "") {
        return false;
    }
    var nextSelect = $(obj).closest('td').next().find('select');
    if (nextSelect.length > 0) {
        var selected = nextSelect.val();
        ajax_get('/api/organization/' + $(obj).val(), {}).done(function(result) {
            nextSelect.empty();
            if (result.children.length == 0) {
                nextSelect.append("<option value=''>---------------</option>");
            }
            $.each(result.children, function(i, item) {
                if (i == 0) {
                    nextSelect.append("<option value=''>---------------</option>");
                }
                nextSelect.append("<option value=" + item.id + ">" + item.name + "</option>");
            });
            nextSelect.val(selected);
        });
    }
}
