<#--
  Assay layout for every Keycloak login page: the "Private demo" strip, the wordmark, one card and a way back to
  the app. Based on base/login/template.ftl (Keycloak 26.8); its scripts are kept as they are.
-->
<#import "footer.ftl" as loginFooter>
<#macro registrationLayout bodyClass="" displayInfo=false displayMessage=true displayRequiredFields=false>
<#assign pageHeading><#nested "header"></#assign>
<#-- Where "Back to Assay" goes: the app's origin (ASSAY_SPA_ORIGIN), so it works even when Keycloak has no client to
     link back to (e.g. the switched-off account console). The app's own base URL is the fallback. -->
<#global appUrl = properties.assayAppUrl!((client.baseUrl)!"")>
<!DOCTYPE html>
<html class="${properties.kcHtmlClass!}" lang="${lang}"<#if realm.internationalizationEnabled> dir="${(locale.rtl)?then('rtl','ltr')}"</#if>>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <meta name="color-scheme" content="light dark">
    <#assign pageTitle = pageHeading?markup_string?replace("<[^>]*>", "", "r")?trim>
    <title>${pageTitle}<#if !pageTitle?contains("Assay")> · Assay</#if></title>
    <link rel="icon" type="image/svg+xml" href="${url.resourcesPath}/img/favicon.svg">
    <link rel="preload" href="${url.resourcesPath}/fonts/ibm-plex-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="${url.resourcesPath}/fonts/ibm-plex-sans-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link href="${url.resourcesPath}/${style}" rel="stylesheet">
        </#list>
    </#if>
    <script type="importmap">
        {
            "imports": {
                "rfc4648": "${url.resourcesCommonPath}/vendor/rfc4648/rfc4648.js"
            }
        }
    </script>
    <#if scripts??>
        <#list scripts as script>
            <script src="${script}" type="text/javascript"></script>
        </#list>
    </#if>
    <script type="module">
        <#outputformat "JavaScript">
        import { startSessionPolling } from ${(url.resourcesPath + "/js/authChecker.js")?c};

        startSessionPolling(
            ${url.ssoLoginInOtherTabsUrl?c}
        );
        </#outputformat>
    </script>
    <script type="module">
        document.addEventListener("click", (event) => {
            const link = event.target.closest("a[data-once-link]");
            if (!link) {
                return;
            }
            if (link.getAttribute("aria-disabled") === "true") {
                event.preventDefault();
                return;
            }
            const { disabledClass } = link.dataset;
            if (disabledClass) {
                link.classList.add(...disabledClass.trim().split(/\s+/));
            }
            link.setAttribute("role", "link");
            link.setAttribute("aria-disabled", "true");
        });
    </script>
    <#if authenticationSession??>
        <script type="module">
            <#outputformat "JavaScript">
            import { checkAuthSession } from ${(url.resourcesPath + "/js/authChecker.js")?c};

            checkAuthSession(
                ${authenticationSession.authSessionIdHash?c}
            );
            </#outputformat>
        </script>
    </#if>
</head>

<body class="${properties.kcBodyClass!} ${bodyClass}" data-page-id="login-${pageId}">
<a class="as-skip" href="#kc-page-title">${msg("assaySkipToContent")}</a>
<div role="region" aria-label="${msg("assayDemoRegion")}" class="as-demo">
    <p class="as-demo-inner">
        <span class="as-ic as-ic-lock" aria-hidden="true"></span>
        <strong>${msg("assayDemoTitle")}</strong>
        <span class="as-demo-sep" aria-hidden="true">·</span>
        <span>${kcSanitize(msg("assayDemoText"))?no_esc}</span>
    </p>
</div>

<div class="${properties.kcLoginClass!}">
    <header class="as-top">
        <#if appUrl?has_content>
            <a class="as-wordmark" href="${appUrl}" aria-label="${msg("assayHome")}">
        <#else>
            <span class="as-wordmark">
        </#if>
            <svg width="26" height="26" viewBox="0 0 40 40" aria-hidden="true" focusable="false">
                <rect x="1.5" y="1.5" width="37" height="37" rx="9" fill="none" stroke="currentColor" stroke-width="3.5"/>
                <path d="M8 23h4.5v8H8zM14.5 19H19v12h-4.5zM21 15h4.5v16H21zM27.5 11H32v20h-4.5z" fill="currentColor"/>
            </svg>
            <b>assay</b>
        <#if appUrl?has_content></a><#else></span></#if>
    </header>

    <main class="as-card">
        <#if realm.internationalizationEnabled && locale.supported?size gt 1>
            <nav class="as-locales" aria-label="${msg("languages")}">
                <#list locale.supported as l>
                    <a href="${l.url}" lang="${l.languageTag}"<#if l.languageTag == locale.currentLanguageTag> aria-current="true"</#if>>${l.label}</a>
                </#list>
            </nav>
        </#if>

        <#if !(auth?has_content && auth.showUsername() && !auth.showResetCredentials())>
            <h1 id="kc-page-title" tabindex="-1">${pageHeading?no_esc}</h1>
        <#else>
            <h1 id="kc-page-title" tabindex="-1">${pageHeading?no_esc}</h1>
            <#nested "show-username">
            <div id="kc-username" class="as-username">
                <span class="as-username-label">${msg("assaySigningInAs")}</span>
                <strong id="kc-attempted-username">${auth.attemptedUsername}</strong>
                <a id="reset-login" class="as-link" href="${url.loginRestartFlowUrl}">${msg("restartLoginTooltip")}</a>
            </div>
        </#if>

        <#if displayRequiredFields>
            <p class="as-help"><span class="required" aria-hidden="true">*</span> ${msg("requiredFields")}</p>
        </#if>

        <#-- App-initiated actions should not see warning messages about the need to complete the action during login. -->
        <#if displayMessage && message?has_content && (message.type != 'warning' || !isAppInitiatedAction??)>
            <div class="${properties.kcAlertClass!} as-alert-${message.type}" role="<#if message.type = 'error' || message.type = 'warning'>alert<#else>status</#if>">
                <#if message.type = 'success'><span class="${properties.kcFeedbackSuccessIcon!}" aria-hidden="true"></span></#if>
                <#if message.type = 'warning'><span class="${properties.kcFeedbackWarningIcon!}" aria-hidden="true"></span></#if>
                <#if message.type = 'error'><span class="${properties.kcFeedbackErrorIcon!}" aria-hidden="true"></span></#if>
                <#if message.type = 'info'><span class="${properties.kcFeedbackInfoIcon!}" aria-hidden="true"></span></#if>
                <span class="${properties.kcAlertTitleClass!}">${kcSanitize(message.summary)?no_esc}</span>
            </div>
        </#if>

        <#nested "form">

        <#if auth?has_content && auth.showTryAnotherWayLink()>
            <form id="kc-select-try-another-way-form" action="${url.loginAction}" method="post">
                <input type="hidden" name="tryAnotherWay" value="on"/>
                <button type="submit" class="as-btn as-btn-link" id="try-another-way">${msg("doTryAnotherWay")}</button>
            </form>
        </#if>

        <#if switchOrganizationEnabled?? && switchOrganizationEnabled>
            <form id="kc-switch-organization-form" action="${url.loginAction}" method="post">
                <input type="hidden" name="switchOrganization" value="true"/>
                <button type="submit" class="as-btn as-btn-link" id="switch-organization">${msg("doSwitchOrganization")}</button>
            </form>
        </#if>

        <#nested "socialProviders">

        <#if displayInfo>
            <div id="kc-info" class="${properties.kcSignUpClass!}">
                <div id="kc-info-wrapper" class="${properties.kcInfoAreaWrapperClass!}">
                    <#nested "info">
                </div>
            </div>
        </#if>

        <@loginFooter.content/>
    </main>

    <footer class="as-foot">
        <#-- error, info and logout-confirm already offer "Back to Assay" in the card. -->
        <#if appUrl?has_content && !["error", "info", "logout-confirm"]?seq_contains(pageId)>
            <a class="as-link" href="${appUrl}">${msg("assayBackToApp")}</a>
        </#if>
        <span>${msg("assayFooter")}</span>
    </footer>
</div>
</body>
</html>
</#macro>
