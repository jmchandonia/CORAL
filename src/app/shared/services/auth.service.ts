import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  constructor(
    private http: HttpClient
  ) { }

  private test = false;

  isAuthenticated() {
    return this.test;
  }

  changeTest() {
  }

  submitLogin(username, password) {
    this.http.post<any>('https://psnov1.lbl.gov:8082/generix/user_login', {username, password})
      .subscribe(res => {
        console.log('RES', res);
      });
  }

}
