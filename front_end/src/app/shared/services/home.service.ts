import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { QueryParam } from '../models/QueryBuilder';
import { environment } from 'src/environments/environment';
import { Subject, EMPTY } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { BsModalService } from 'ngx-bootstrap/modal';
import { ErrorComponent } from 'src/app/shared/components/error/error.component';
@Injectable({
  providedIn: 'root'
})
export class HomeService {

  constructor(
    private http: HttpClient,
    private modalService: BsModalService
    ) { }

  provenanceGraphSub: Subject<any> = new Subject();
  provenanceLoadingSub: Subject<any> = new Subject();

  getFilterValues() {
    return this.http.get(`${environment.baseURL}/filters`);
  }

  getUpdatedValues(filterQuery: QueryParam[]) {
   return this.http.post<any>(`${environment.baseURL}/types_stat`, filterQuery);
  }

  getReports() {
    return this.http.get(`${environment.baseURL}/reports`);
  }

  getReportItem(id: string) {
    return this.http.get(`${environment.baseURL}/reports/${id}`);
  }

  getProvenanceGraphData(filterQuery?: QueryParam[]) {
    this.provenanceLoadingSub.next(true); // tell component to display loading animation
    if (filterQuery) {
      this.http.post(`${environment.baseURL}/types_graph`, filterQuery)
        .subscribe(data => this.provenanceGraphSub.next(data));
    } else {
      this.http.get(`${environment.baseURL}/types_graph`)
        .subscribe(data => this.provenanceGraphSub.next(data));
    }
  }

  getProvenanceGraphSub() {
    return this.provenanceGraphSub.asObservable();
  }

  getProvenanceLoadingSub() {
    return this.provenanceLoadingSub.asObservable();
  }

  setNodePositionCache(cacheKey: string, id: number, {x, y}) {
    return this.http.post(`${environment.baseURL}/set_node_position_cache`, {x, y, cacheKey, id}).toPromise();
  }

  initBackendConnection() {
    // test if back end is running
    return this.http.get(environment.baseURL + '/', {
      headers: new HttpHeaders({
        'Content-Type': 'text/plain; charset=utf-8'
      }),
      responseType: 'text'
    })
      .pipe(
        // warn user if backend connection fails
        catchError(e => {
          //  TODO: This should be thrown as an error, but throwing it adds stack trace info not useful to the user
          this.modalService.show(ErrorComponent, {
            class: 'modal-lg',
            initialState: {
              message: `Connection to API at ${environment.baseURL} failed. Please check your internet connection or contact your site administrator.`
            }
          })
          return EMPTY;
        })
      ).toPromise();
  }

}
