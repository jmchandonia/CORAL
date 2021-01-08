import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { JwtHelperService } from '@auth0/angular-jwt';
import { environment } from 'src/environments/environment';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  public redirectUrl: string;

  constructor(
    private http: HttpClient,
    public jwtHelper: JwtHelperService,
    private router: Router
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

  logout() {
    localStorage.removeItem('authToken');
    // localStorage.clear();
  }

}
