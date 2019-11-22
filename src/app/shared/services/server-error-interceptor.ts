import { Injectable } from '@angular/core';
import {
    HttpEvent,
    HttpRequest,
    HttpHandler,
    HttpInterceptor,
    HttpErrorResponse,
    HttpResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { retry, catchError, tap } from 'rxjs/operators';

@Injectable()

export class ServerErrorInterceptor implements HttpInterceptor {

    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        return next.handle(request)
        .pipe(
            retry(1),
            catchError((error: HttpErrorResponse) => {
                // catch status code errors
                return throwError(error);
            }),
            tap((event: HttpResponse<any>) => {
                // catch errors that come as JSON response from server
                const { body } = event;
                if (body && body.error) {
                    throw new Error(body.error);
                }
            }),
        );
    }

}
