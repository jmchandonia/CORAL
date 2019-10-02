import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../shared/services/auth.service';
import { NgxSpinnerService } from 'ngx-spinner';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {

  constructor(
    private router: Router,
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
        if (res.success) {
          this.router.navigate(['home']);
        } else {
          this.error = true;
          this.errorMessage = res.message;
        }
      });
  }

}
