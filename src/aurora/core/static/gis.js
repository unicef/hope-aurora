;(function ($) {
    $(function () {
        console.log(1111);
        if (window.navigator.geolocation) {
        console.log(1111.2);
            window.navigator.geolocation
                  .getCurrentPosition(function (res) {
                      var data = {
                          accuracy: res.coords.accuracy,
                          altitude: res.coords.altitude,
                          altitudeAccuracy: res.coords.altitudeAccuracy,
                          heading: res.coords.heading,
                          latitude: res.coords.latitude,
                          longitude: res.coords.longitude,
                          speed: res.coords.speed
                      };
        console.log(1111.3, data);

                      $(".vLocationField").each(function () {
                          $(this).val(btoa(JSON.stringify(data)));
                      });

                  }, function (err) {
                      $(this).val(err);
                  });
        }
    });
})(jQuery || django.jQuery);
