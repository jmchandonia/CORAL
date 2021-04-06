import { Injectable } from '@angular/core';
import { User } from '../models/user';
import { HttpClient } from  '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class UserService {

  private user: User = null;

  constructor(
    private http: HttpClient
  ) { }

  addTerm() {}

  addTermCollection() {}

  setUser(user: User) {
    this.user = user;
    localStorage.setItem('user', JSON.stringify(user))
  }

  getUser(): User {
    return this.user ?? JSON.parse(localStorage.getItem('user'));
  }

}
