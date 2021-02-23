import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../../shared/services/auth.service';
import { NgxSpinnerService } from 'ngx-spinner';
import { environment } from 'src/environments/environment';
declare var gapi: any;
@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {

  private gapiSetup = false;
  // private googleAuthInstance: gapi.auth2.GoogleAuth;
  private googleAuthInstance: any;

  constructor(
    private auth: AuthService,
    private spinner: NgxSpinnerService
  ) { }
  public displayLogin = true;
  public error = false;
  public loading = false;
  public errorMessage = '';
  username = '';
  password = '';

  ngOnInit() {
  }

  login() {
    this.loading = true;
    this.spinner.show();
    this.auth.submitLogin(this.username, this.password)
      .subscribe(res => {
        this.spinner.hide();
        this.loading = false;
        if (!res.success) {
          this.error = true;
          this.errorMessage = res.message;
        }
      });
  }

  async initGoogleAuth(): Promise<void> {
    const pload = new Promise((resolve) => {
      gapi.load('auth2', resolve);
    });

    return pload.then(async () => {
      await gapi.auth2
        .init({
          client_id: environment.GOOGLE_OAUTH2_CLIENT_KEY,
          // ux_mode: 'redirect',
          // redirect_uri: `${environment.baseURL}/google_oauth_callback`
        })
        .then(auth => {
          this.gapiSetup = true;
          this.googleAuthInstance = auth;
          // console.log('GOOGLE AUTH IS ALL SET UP', this.googleAuthInstance);
        });
    });
  }

  async handleGoogleAuthSignIn() {
    console.log('Signing in with google...');
    if (!this.gapiSetup) {
      await this.initGoogleAuth();
    }

    // return new Promise(async () => {
    //   await this.googleAuthInstance.signIn().then(
    //     user => console.log('user', user),
    //     error => console.log('error', error)
    //   );
    // });
    await this.googleAuthInstance.grantOfflineAccess().then(
      data => this.handleSigninCode(data.code),
      err => console.error(err)
    );
  }

  handleSigninCode(code: string) {
    console.log('CODE', code);
    this.auth.submitGoogleOAuthCode(code)
      .subscribe(data => {
        console.log('DATA', data);
      })
  }

}
