import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { SearchComponent } from './search.component';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';

describe('SearchComponent', () => {

  let spectator: Spectator<SearchComponent>;
  const createComponent = createComponentFactory({
    component: SearchComponent,
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
