<#-- "Sign out?" (shown when a sign-out request has no id_token_hint). Same form as base/login/logout-confirm.ftl (Keycloak 26.8), as two buttons. -->
<#import "template.ftl" as layout>
<@layout.registrationLayout; section>
    <#if section = "header">
        ${msg("logoutConfirmTitle")}
    <#elseif section = "form">
        <div id="kc-logout-confirm">
            <p class="instruction">${msg("logoutConfirmHeader")}</p>
            <form class="as-actions" action="${url.logoutConfirmAction}" onsubmit="confirmLogout.disabled = true; return true;" method="POST">
                <input type="hidden" name="session_code" value="${logoutConfirm.code}">
                <input class="${properties.kcButtonClass!} ${properties.kcButtonPrimaryClass!}" name="confirmLogout" id="kc-logout" type="submit" value="${msg("doLogout")}"/>
                <#if !logoutConfirm.skipLink && appUrl?has_content>
                    <a class="${properties.kcButtonClass!} ${properties.kcButtonSecondaryClass!}" href="${appUrl}">${msg("backToApplication")}</a>
                </#if>
            </form>
        </div>
    </#if>
</@layout.registrationLayout>
