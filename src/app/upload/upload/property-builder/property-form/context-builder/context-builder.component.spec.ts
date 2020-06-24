import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { ContextBuilderComponent } from './context-builder.component';
import { MockComponent } from 'ng-mocks';
import { ContextFormComponent } from './context-form/context-form.component';
import { ModalModule, BsModalRef } from 'ngx-bootstrap/modal';
import { HttpClientModule } from '@angular/common/http';

describe('ContextBuilderComponent', () => {
  let spectator: Spectator<ContextBuilderComponent>;
  const createComponent = createComponentFactory({
    component: ContextBuilderComponent,
    entryComponents: [
      MockComponent(ContextFormComponent)
    ],
    imports: [
      ModalModule.forRoot(),
      HttpClientModule
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
