import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { ErrorComponent } from './error.component';
import { RouterModule } from '@angular/router';
import { BsModalRef } from 'ngx-bootstrap/modal';

describe('ErrorComponent', () => {
  let spectator: Spectator<ErrorComponent>;
  const createComponent = createComponentFactory({
    component: ErrorComponent,
    imports: [
      RouterModule.forRoot([])
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
