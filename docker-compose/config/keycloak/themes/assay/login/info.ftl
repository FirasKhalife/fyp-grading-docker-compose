<#--
  Keycloak's info page ("You're signed out", "You're already signed in", …). Same links as base/login/info.ftl
  (Keycloak 26.8); the message is shown once, as the heading, unless a separate header is set.
-->
<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=false; section>
    <#if section = "header">
        <#if messageHeader??>
            ${kcSanitize(msg("${messageHeader}"))?no_esc}
        <#else>
            ${message.summary}
        </#if>
    <#elseif section = "form">
        <div id="kc-info-message">
            <#if messageHeader?? || requiredActions??>
                <p class="instruction">${message.summary}<#if requiredActions??><#list requiredActions>: <b><#items as reqActionItem>${kcSanitize(msg("requiredAction.${reqActionItem}"))?no_esc}<#sep>, </#items></b></#list></#if></p>
            <#else>
                <p class="instruction">${msg("assayInfoText")}</p>
            </#if>
            <#if !skipLink??>
                <#if pageRedirectUri?has_content>
                    <p class="as-actions"><a class="as-btn as-btn-primary" href="${pageRedirectUri}">${msg("backToApplication")}</a></p>
                <#elseif actionUri?has_content>
                    <p class="as-actions"><a class="as-btn as-btn-primary" href="${actionUri}">${msg("proceedWithAction")}</a></p>
                <#elseif (client.baseUrl)?has_content>
                    <p class="as-actions"><a class="as-btn as-btn-primary" href="${client.baseUrl}">${msg("backToApplication")}</a></p>
                </#if>
            </#if>
        </div>
    </#if>
</@layout.registrationLayout>
