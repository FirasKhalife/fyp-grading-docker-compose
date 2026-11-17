<#-- "Page has expired" (e.g. the back button after signing in): two real buttons instead of two "click here" links. Follows base/login/login-page-expired.ftl (Keycloak 26.8). -->
<#import "template.ftl" as layout>
<@layout.registrationLayout; section>
    <#if section = "header">
        ${msg("pageExpiredTitle")}
    <#elseif section = "form">
        <p class="instruction">${msg("assayPageExpiredText")}</p>
        <div class="as-actions">
            <a id="loginRestartLink" class="as-btn as-btn-primary" href="${url.loginRestartFlowUrl}">${msg("assayPageExpiredRestart")}</a>
            <a id="loginContinueLink" class="as-btn as-btn-secondary" href="${url.loginAction}">${msg("assayPageExpiredContinue")}</a>
        </div>
    </#if>
</@layout.registrationLayout>
