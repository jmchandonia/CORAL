import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class NetworkService {

  private networkSub: Subject<any> = new Subject();

  private dataTypeStore = {
    queryMatch: [],
    connectsUpTo: [],
    connectsDownTo: [],
  }

  constructor(private _http: HttpClient) { }

  getDataTypeProperties(dataType, connection) {
    this._http.get('https://jsonplaceholder.typicode.com/posts')
    .subscribe(results => {
      this.dataTypeStore[connection] = results;
      this.networkSub.next({
        connection: connection,
        results: results
      })
    });
  }

  getPropertyValuesDirect(connection) {
    return this.dataTypeStore[connection];
  }

  getPropertyValues() {
    return this.networkSub.asObservable();
  }


}
