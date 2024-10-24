;(function ($) {
    $(function () {
        const $start = $("input.CompilationTimeField.start");
        const $round = $("input.CompilationTimeField.round");
        const formInitializationTime = new Date();
        var start = formInitializationTime;
        var first = $start.val();
        var currentVal = 0;
        var elapsed = 0;
        var total = 0;

        if (first === undefined || first === '') {
            $start.val( formInitializationTime );
        } else {
            currentVal = parseInt($round.val() || 0);
            start = Date.parse( $start.val() )
        }
        $round.val(currentVal);

        $("#registrationForm").bind("submit", function (e) {
            currentVal++;
            elapsed = new Date() - formInitializationTime;
            total = new Date() - start;
            $("input.CompilationTimeField.elapsed").val(elapsed);
            $("input.CompilationTimeField.total").val(total);
            $round.val(currentVal);
        });
    });
})(jQuery);
