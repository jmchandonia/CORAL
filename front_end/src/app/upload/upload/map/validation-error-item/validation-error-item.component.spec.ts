import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { HttpClientModule } from '@angular/common/http';
import { ModalModule, BsModalRef } from 'ngx-bootstrap/modal';
import { ValidationErrorItemComponent } from './validation-error-item.component';

xdescribe('ValidationErrorItemComponent', () => {
  let spectator: Spectator<ValidationErrorItemComponent>;
  const createComponent = createComponentFactory({
    component: ValidationErrorItemComponent,
    imports: [
      HttpClientModule,
      ModalModule.forRoot()
    ],
    providers: [
      BsModalRef
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
