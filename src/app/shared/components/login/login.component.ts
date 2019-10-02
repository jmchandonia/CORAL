import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../shared/services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {

  constructor(
    private router: Router,
    private auth: AuthService
  ) { }
  public displayLogin = true;
  public error = false;
  public errorMessage = '';
  username = '';
  password = '';

  ngOnInit() {
  }

  login() {
    this.auth.submitLogin(this.username, this.password)
      .subscribe(res => {
        if (res.success) {
          this.router.navigate(['home']);
        } else {
          this.error = true;
          this.errorMessage = res.message;
        }
      });
  }

}
