import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { AuthService } from '../../../shared/services/auth.service';
import { NgxSpinnerService } from 'ngx-spinner';
import { environment } from 'src/environments/environment';
import { BsModalRef, BsModalService } from 'ngx-bootstrap/modal';
import { UserRegistrationComponent } from './user-registration/user-registration.component';
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
  modalRef: BsModalRef

  constructor(
    private auth: AuthService,
    private spinner: NgxSpinnerService,
    private chRef: ChangeDetectorRef,
    private modalService: BsModalService
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
        })
        .then(auth => {
          this.gapiSetup = true;
          this.googleAuthInstance = auth;
        });
    });
  }

  async handleGoogleAuthSignIn() {
    if (!this.gapiSetup) {
      await this.initGoogleAuth();
    }

    await this.googleAuthInstance.grantOfflineAccess().then(
      data => this.handleSigninCode(data),
      err => console.error(err)
    );
  }

  handleSigninCode(data: any) {
    this.auth.submitGoogleOAuthCode(data.code)
      .subscribe(res => {
        if (!res.results.success) {
          this.error = true;
          this.errorMessage = res.results.message;
          this.chRef.detectChanges();
        }
      })
  }

  displayRegistrationForm() {
    this.modalRef = this.modalService.show(UserRegistrationComponent, {
      class: 'modal-lg'
    })
  }


}
