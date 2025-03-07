var script = document.getElementById("script-sentry");
const pk = $("meta[name=\"RegId\"]").attr("content");
const slug = $("meta[name=\"Survey\"]").attr("content");
const organization = $("meta[name=\"Organization\"]").attr("content");
const project = $("meta[name=\"Project\"]").attr("content");
Sentry.init({
    dsn: script.dataset.dsn,
    release: script.dataset.version,
    tracesSampleRate: 1.0,
    ignoreErrors: [
        "datepicker.inputField.after is not a function",
        "num.toString(...).padStart is not a function",
        "Unexpected token =>",
        "Unexpected identifier",
    ]
});
if (slug){
    Sentry.setTag("registration.slug", slug);
    Sentry.setTag("registration.organization", organization);
    Sentry.setTag("registration.project", project);
}
