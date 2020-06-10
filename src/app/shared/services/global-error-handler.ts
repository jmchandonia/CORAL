import { Injector, ErrorHandler, Injectable, NgZone } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { BsModalRef, BsModalService } from 'ngx-bootstrap';
import { ErrorComponent } from 'src/app/shared/components/error/error.component';
import { TemplateParseError } from '@angular/compiler';
import { Router, NavigationEnd } from '@angular/router';

@Injectable()

export class GlobalErrorHandler implements ErrorHandler {

    private modalRef: BsModalRef;
    private modalService: BsModalService;
    private router: Router;

    constructor(private injector: Injector, private zone: NgZone) {
        setTimeout(() => {
            this.modalService = this.injector.get(BsModalService);
            this.router = this.injector.get(Router);
        });
    }

    errorMessage = '';

    handleError(error: Error | HttpErrorResponse) {
        if (error instanceof HttpErrorResponse) {
            const {status, message} = error;
            this.zone.run(() => {
                const config = {
                    class: 'modal-lg',
                    initialState: {status, message}
                };
                this.modalRef = this.modalService.show(ErrorComponent, config);
            });
            console.error(error);
            throw error;
        } else {
            console.error(error)
            if(this.errorMessage !== error.message) { // prevents concurrent errors from components to raise more than once
                this.zone.runOutsideAngular(() => {
                    const config = {
                        class: 'modal-lg',
                        initialState: { message: error.message }
                    };
                    this.modalRef = this.modalService.show(ErrorComponent, config);
                    this.errorMessage = error.message;
                    console.error(error);
                    this.router.events.subscribe(event => {
                        if (event instanceof NavigationEnd) {
                            this.errorMessage = '';
                        }
                    });
                });
            } else {
                console.error(error);
            }
        }
    }
}
