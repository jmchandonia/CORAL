import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { LoadComponent } from './load.component';
import { MockComponent } from 'ng-mocks';
import { LoadSuccessTableComponent } from './load-success-table/load-success-table.component';

describe('LoadComponent', () => {
  let spectator: Spectator<LoadComponent>;
  const createComponent = createComponentFactory({
    component: LoadComponent,
    imports: [
      NgxSpinnerModule,
      HttpClientModule
    ],
    entryComponents: [
      MockComponent(LoadSuccessTableComponent)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
