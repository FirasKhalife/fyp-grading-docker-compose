<#-- Keycloak's error page (bad link, stale page, lost cookie): a plain explanation first, Keycloak's own reason below. Follows base/login/error.ftl (Keycloak 26.8). -->
<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=false; section>
    <#if section = "header">
        ${msg("errorTitle")}
    <#elseif section = "form">
        <div id="kc-error-message">
            <p class="instruction">${msg("assayErrorText")}</p>
            <p class="as-detail">${kcSanitize(message.summary)?no_esc}</p>
            <#if traceId??>
                <p class="as-detail" id="traceId">${msg("traceIdSupportMessage", traceId)}</p>
            </#if>
            <#if !skipLink?? && client?? && client.baseUrl?has_content>
                <p class="as-actions"><a id="backToApplication" class="as-btn as-btn-primary" href="${client.baseUrl}">${msg("backToApplication")}</a></p>
            </#if>
        </div>
    </#if>
</@layout.registrationLayout>
