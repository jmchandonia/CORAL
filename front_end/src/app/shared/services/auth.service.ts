import { Injectable, NgZone } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { JwtHelperService } from '@auth0/angular-jwt';
import { environment } from 'src/environments/environment';
import { Router } from '@angular/router';
import { Response } from 'src/app/shared/models/response';
import { UserService } from 'src/app/shared/services/user.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  public redirectUrl: string;

  constructor(
    private http: HttpClient,
    public jwtHelper: JwtHelperService,
    private router: Router,
    private zone: NgZone,
    private userService: UserService
  ) { }


  isAuthenticated() {
    const token = localStorage.getItem('authToken');
    if (!token) {
      return false;
    } else {
      return !this.jwtHelper.isTokenExpired(token);
     }
  }

  submitLogin(username, password) {
    return this.http.post<any>(`${environment.baseURL}/user_login`, {username, password})
      .pipe(map(res => {
        const success = res.success;
        if (success) {
          localStorage.setItem('authToken', res.token);
          if (this.redirectUrl) {
            this.router.navigateByUrl(this.redirectUrl);
            this.redirectUrl = null;
          } else {
            this.router.navigate(['home']);
          }
        }
        return res;
      }));
  }

  submitGoogleOAuthCode(authCode: string) {
    return this.http.post<any>(`${environment.baseURL}/google_auth_code_store`, {authCode})
      .pipe(map((res) => {
        const { results } = res;
        const success = results.success;
        if (success) {
          localStorage.setItem('authToken', results.token);
          this.userService.setUser(results.user);
          if (this.redirectUrl) {
            this.zone.run(() => {
              this.router.navigateByUrl(this.redirectUrl);
            });
            this.redirectUrl = null;
          } else {
            this.zone.run(() => {
              this.router.navigate(['/home']);
            });
          }
        }
        return res;
      }));
  }

  logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    // localStorage.clear();
  }

}
