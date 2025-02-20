;(function ($) {
    $(function () {
        if (window.navigator.geolocation) {
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

                      $(".vLocationField").each(function () {
                          $(this).val(btoa(JSON.stringify(data)));
                      });

                  }, function (err) {
                      $(this).val(err);
                  });
        }
    });
})(jQuery);
