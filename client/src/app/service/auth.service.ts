import {Injectable} from '@angular/core';
import { User, UserManager } from 'oidc-client-ts';
import {BehaviorSubject} from "rxjs";
import {HttpClient} from "@angular/common/http";
import { environment } from '../../environments/environment';

export type Settings = {
  endpoint: string;
  clientID: string;
  pool: string;
  langgraph_api_key: string;
};

@Injectable({
  providedIn: 'root',
})
export class AuthService {

  userManager!: UserManager;
  private readySubject = new BehaviorSubject<boolean>(false);


  constructor(private httpClient: HttpClient) {
    if (environment.useLocalSettings) {
      this.initializeUserManager(environment.localSettings);
    } else {
      this.httpClient.get<Settings>('/settings').subscribe(properties => {
        this.initializeUserManager(properties);
      });
    }
  }

  private initializeUserManager(properties: Settings) {
    console.log(properties);
    const settings = {
      authority: `https://${properties.pool}.auth.us-east-1.amazoncognito.com`,
      client_id: properties.clientID,
      redirect_uri: `${window.location.protocol}//${window.location.host}/signin-callback`,
      silent_redirect_uri: `${window.location.protocol}//${window.location.host}/silent-callback.html`,
      post_logout_redirect_uri: `${window.location.protocol}//${window.location.host}`,
      response_type: 'code',
      scope: 'openid',
      automaticSilentRenew: true,
      filterProtocolClaims: true,
      loadUserInfo: true,
      validateSubOnSilentRenew: true,

      metadata: {
        authorization_endpoint: `https://${properties.pool}.auth.us-east-1.amazoncognito.com/oauth2/authorize`,
        end_session_endpoint: `https://${properties.pool}.auth.us-east-1.amazoncognito.com/logout?client_id=${properties.clientID}&redirect_uri=${window.location.protocol}//${window.location.host}callback.html&response_type=code`,
        issuer: `https://cognito-idp.us-east-1.amazonaws.com/${properties.pool}`,
        jwks_uri: `https://cognito-idp.us-east-1.amazonaws.com/${properties.pool}/.well-known/jwks.json`,
        response_types_supported: ['code', 'token'],
        revocation_endpoint: `https://${properties.pool}.auth.us-east-1.amazoncognito.com/oauth2/revoke`,
        scopes_supported: ['openid', 'email', 'phone', 'profile'],
        subject_types_supported: ['public'],
        token_endpoint: `https://${properties.pool}.auth.us-east-1.amazoncognito.com/oauth2/token`,
        token_endpoint_auth_methods_supported: [
          'client_secret_basic',
          'client_secret_post',
        ],
        userinfo_endpoint: `https://${properties.pool}.auth.us-east-1.amazoncognito.com/oauth2/userInfo`,
        token_endpoint_auth_signing_alg_values_supported: ['RS256'],
      }
    };
    this.userManager = new UserManager(settings);
    this.readySubject.next(true);
    console.log('finished initialising user manager');
  }

  getUser(): Promise<User | null> {
    return this.userManager.getUser();
  }

  login(): Promise<void> {
    return this.userManager.signinRedirect();
  }

  renewToken(): Promise<User | null> {
    return this.userManager.signinSilent();
  }

  logout(): Promise<void> {
    return this.userManager.signoutRedirect();
  }

  getReadySubject(): BehaviorSubject<boolean> {
    return this.readySubject
  }

}
