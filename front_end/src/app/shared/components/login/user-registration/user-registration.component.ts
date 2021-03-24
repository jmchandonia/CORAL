import { Component, OnInit, ElementRef, ViewChild, NgZone } from '@angular/core';
import { environment } from 'src/environments/environment';
import { AuthService } from 'src/app/shared/services/auth.service';

declare const grecaptcha: any;
declare global {
  interface Window {
    grecaptcha: any;
    reCaptchaLoad: () => void;
  }
}

@Component({
  selector: 'app-user-registration',
  templateUrl: './user-registration.component.html',
  styleUrls: ['./user-registration.component.css']
})
export class UserRegistrationComponent implements OnInit {

  constructor(
    private zone: NgZone,
    private auth: AuthService
  ) { }

  public email: string;
  public firstName: string;
  public lastName: string;
  public siteKey: string;
  private successToken: string;
  widgetId: any;
  submitted = false;

  @ViewChild('reCaptchaWidget') reCaptchaWidget: ElementRef;

  ngOnInit(): void {
    this.siteKey = environment.GOOGLE_CAPTCHA_SITE_KEY;
    this.registerRecaptchaCallback();
    this.addReCaptchaScript();
  }

  registerRecaptchaCallback() {
    window.reCaptchaLoad = () => {
      this.widgetId = grecaptcha.render(this.reCaptchaWidget.nativeElement, {
        'sitekey': environment.GOOGLE_CAPTCHA_SITE_KEY,
        'callback': this.onSuccess.bind(this),
        'expired-callback': this.onExpired.bind(this)
      })
    }
  }

  addReCaptchaScript() {
    const script = document.createElement('script');
    script.src = 'https://www.google.com/recaptcha/api.js?onload=reCaptchaLoad&render=explicit';
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);
  }

  onSuccess(token: string) {
    this.zone.run(() => {
      this.successToken = token;
      this.auth.submitRegistrationRequest(this.firstName, this.lastName, this.email, this.successToken)
      .subscribe((res: any) => {
        if (res.success) {
          this.submitted = true;
        }
      });
    });
  }

  onExpired() {
  }

  get incompleteFields() {
    return this.firstName === undefined ||
    this.lastName === undefined ||
    this.email === undefined ||
    this.successToken === undefined;
  }

  submitRegistrationRequest() {
    this.auth.submitRegistrationRequest(this.firstName, this.lastName, this.email, this.successToken)
      .subscribe((res: any) => {
        if (res.success) {
          this.submitted = true;
        } else {
        }
      });
  }

}
