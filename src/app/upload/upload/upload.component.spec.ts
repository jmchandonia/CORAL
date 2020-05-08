import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { UploadComponent } from './upload.component';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';

describe('UploadComponent', () => {

  let spectator: Spectator<UploadComponent>;
  const createComponent = createComponentFactory({
    component: UploadComponent,
    imports: [
      RouterModule.forRoot([]),
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
