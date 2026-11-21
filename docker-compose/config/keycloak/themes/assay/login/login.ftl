<#--
  The username + password page ("Sign in with username" in the app). Same fields and form posts as
  base/login/login.ftl (Keycloak 26.8), with the Assay copy, natural tab order and the demo username and password hints.
  Registration, password reset and remember-me are off in the realm, so their links are not rendered.
-->
<#import "template.ftl" as layout>
<#import "passkeys.ftl" as passkeys>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('username','password'); section>
    <#if section = "header">
        ${msg("loginAccountTitle")}
    <#elseif section = "form">
        <p class="as-lede">${msg("assayLoginLede")}</p>
        <#if realm.password>
            <form id="kc-form-login" class="as-form" onsubmit="login.disabled = true; return true;" action="${url.loginAction}" method="post" novalidate>
                <#assign hasError = messagesPerField.existsError('username','password')>
                <#if hasError>
                    <div class="${properties.kcAlertClass!} as-alert-error" role="alert" id="input-error">
                        <span class="${properties.kcFeedbackErrorIcon!}" aria-hidden="true"></span>
                        <span class="${properties.kcAlertTitleClass!}">${kcSanitize(messagesPerField.getFirstError('username','password'))?no_esc}</span>
                    </div>
                </#if>

                <#if !usernameHidden??>
                    <div class="${properties.kcFormGroupClass!}">
                        <label for="username" class="${properties.kcLabelClass!}"><#if !realm.loginWithEmailAllowed>${msg("username")}<#elseif !realm.registrationEmailAsUsername>${msg("usernameOrEmail")}<#else>${msg("email")}</#if></label>
                        <input id="username" class="${properties.kcInputClass!}" name="username" value="${(login.username!'')}" type="text"
                               autofocus autocapitalize="none" spellcheck="false"
                               autocomplete="${(enableWebAuthnConditionalUI?has_content)?then('username webauthn', 'username')}"
                               aria-describedby="username-hint<#if hasError> input-error</#if>"
                               <#if hasError>aria-invalid="true"</#if>
                               dir="ltr"/>
                        <p class="as-help" id="username-hint">${kcSanitize(msg("assayUsernameHint"))?no_esc}</p>
                    </div>
                </#if>

                <div class="${properties.kcFormGroupClass!}">
                    <label for="password" class="${properties.kcLabelClass!}">${msg("password")}</label>
                    <div class="${properties.kcInputGroup!}" dir="ltr">
                        <input id="password" class="${properties.kcInputClass!}" name="password" type="password" autocomplete="current-password"
                               aria-describedby="password-hint<#if hasError> input-error</#if>"
                               <#if hasError>aria-invalid="true"</#if>/>
                        <button class="${properties.kcFormPasswordVisibilityButtonClass!}" type="button" aria-label="${msg("showPassword")}"
                                aria-controls="password" data-password-toggle
                                data-icon-show="${properties.kcFormPasswordVisibilityIconShow!}" data-icon-hide="${properties.kcFormPasswordVisibilityIconHide!}"
                                data-label-show="${msg('showPassword')}" data-label-hide="${msg('hidePassword')}">
                            <i class="${properties.kcFormPasswordVisibilityIconShow!}" aria-hidden="true"></i>
                        </button>
                    </div>
                    <p class="as-help" id="password-hint">${kcSanitize(msg("assayPasswordHint"))?no_esc}</p>
                </div>

                <#if realm.resetPasswordAllowed>
                    <p class="as-form-options"><a class="as-link" href="${url.loginResetCredentialsUrl}">${msg("doForgotPassword")}</a></p>
                </#if>

                <div id="kc-form-buttons">
                    <input type="hidden" id="id-hidden-input" name="credentialId" <#if auth.selectedCredential?has_content>value="${auth.selectedCredential}"</#if>/>
                    <input class="${properties.kcButtonClass!} ${properties.kcButtonPrimaryClass!} ${properties.kcButtonBlockClass!}" name="login" id="kc-login" type="submit" value="${msg("doLogIn")}"/>
                </div>
            </form>
        </#if>
        <@passkeys.conditionalUIData />
        <script type="module" src="${url.resourcesPath}/js/passwordVisibility.js"></script>
    </#if>
</@layout.registrationLayout>
